from __future__ import annotations

import asyncio
import json as jsonlib
from collections.abc import AsyncIterator
from typing import Any

import httpx
import structlog

from app.ai.exceptions import GenerationError, ProviderUnavailableError, TimeoutError

logger = structlog.get_logger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class AIHTTPClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: int = 60,
        max_retries: int = 3,
        retry_delay_seconds: int = 1,
        api_key: str | None = None,
        default_headers: dict[str, str] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        if default_headers:
            headers.update(default_headers)
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            timeout=httpx.Timeout(timeout_seconds),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )
        self._default_headers = headers

    async def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        *,
        retry_on: set[int] | None = None,
    ) -> httpx.Response:
        retry_codes = retry_on or RETRYABLE_STATUS_CODES
        last_exception: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                response = await self._client.post(path, json=json)
                if response.status_code in retry_codes and attempt < self._max_retries:
                    wait = self._backoff(attempt)
                    logger.warning(
                        "Retryable status, retrying",
                        path=path,
                        status=response.status_code,
                        attempt=attempt,
                        wait=wait,
                    )
                    await asyncio.sleep(wait)
                    continue
                if response.status_code == 401:
                    raise GenerationError("Authentication failed: invalid or missing API key")
                if response.status_code == 400:
                    body = self._safe_json(response)
                    msg = "Bad request"
                    if isinstance(body, dict):
                        msg = body.get("error", {}).get("message", "Bad request")
                    raise GenerationError(msg)
                if response.status_code >= 500 and attempt == self._max_retries:
                    raise ProviderUnavailableError(f"Provider returned {response.status_code}")
                response.raise_for_status()
                return response
            except httpx.TimeoutException:
                last_exception = TimeoutError(f"Request timed out after {self._client.timeout.read}s")
                if attempt < self._max_retries:
                    wait = self._backoff(attempt)
                    logger.warning("Timeout, retrying", path=path, attempt=attempt, wait=wait)
                    await asyncio.sleep(wait)
                    continue
            except (httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                last_exception = ProviderUnavailableError(f"Connection failed: {exc}")
                if attempt < self._max_retries:
                    wait = self._backoff(attempt)
                    logger.warning("Connection error, retrying", path=path, attempt=attempt, wait=wait)
                    await asyncio.sleep(wait)
                    continue
            except (GenerationError, ProviderUnavailableError, TimeoutError):
                raise
            except httpx.HTTPStatusError as exc:
                raise ProviderUnavailableError(f"HTTP {exc.response.status_code}: {exc.response.text[:200]}") from exc
            except Exception as exc:
                last_exception = GenerationError(f"Unexpected error: {exc}")
                if attempt < self._max_retries:
                    await asyncio.sleep(self._backoff(attempt))
                    continue

        raise last_exception or ProviderUnavailableError("Request failed after all retries")

    async def get(self, path: str, *, retry_on: set[int] | None = None) -> httpx.Response:
        retry_codes = retry_on or RETRYABLE_STATUS_CODES
        last_exception: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                response = await self._client.get(path)
                if response.status_code in retry_codes and attempt < self._max_retries:
                    await asyncio.sleep(self._backoff(attempt))
                    continue
                response.raise_for_status()
                return response
            except httpx.TimeoutException:
                last_exception = TimeoutError("Request timed out")
                if attempt < self._max_retries:
                    await asyncio.sleep(self._backoff(attempt))
                    continue
            except (httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                last_exception = ProviderUnavailableError(f"Connection failed: {exc}")
                if attempt < self._max_retries:
                    await asyncio.sleep(self._backoff(attempt))
                    continue
            except httpx.HTTPStatusError as exc:
                raise ProviderUnavailableError(f"HTTP {exc.response.status_code}: {exc.response.text[:200]}") from exc
            except Exception as exc:
                last_exception = GenerationError(f"Unexpected error: {exc}")
                if attempt < self._max_retries:
                    await asyncio.sleep(self._backoff(attempt))
                    continue

        raise last_exception or ProviderUnavailableError("Request failed after all retries")

    async def stream(self, path: str, json: dict[str, Any] | None = None) -> AsyncIterator[dict[str, Any]]:
        """POST an SSE request and yield parsed `data:` JSON payloads as they arrive."""
        try:
            async with self._client.stream("POST", path, json=json) as response:
                if response.status_code in RETRYABLE_STATUS_CODES or response.status_code >= 400:
                    body = await response.aread()
                    detail = body[:300].decode("utf-8", errors="replace")
                    if response.status_code == 401:
                        raise GenerationError("Authentication failed: invalid or missing API key")
                    if response.status_code >= 500:
                        raise ProviderUnavailableError(f"Provider returned {response.status_code}")
                    raise GenerationError(detail or f"Provider returned {response.status_code}")
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line.startswith("data:"):
                        continue
                    payload = line[len("data:"):].strip()
                    if not payload or payload == "[DONE]":
                        continue
                    try:
                        yield jsonlib.loads(payload)
                    except jsonlib.JSONDecodeError:
                        logger.warning("Failed to parse SSE chunk", path=path, payload=payload[:200])
        except httpx.TimeoutException:
            raise TimeoutError(f"Stream request timed out after {self._client.timeout.read}s") from None
        except (httpx.ConnectError, httpx.RemoteProtocolError) as exc:
            raise ProviderUnavailableError(f"Connection failed: {exc}") from exc
        except (GenerationError, ProviderUnavailableError, TimeoutError):
            raise
        except httpx.HTTPStatusError as exc:
            raise ProviderUnavailableError(f"HTTP {exc.response.status_code}: {exc.response.text[:200]}") from exc

    def _backoff(self, attempt: int) -> float:
        return self._retry_delay_seconds * (2 ** (attempt - 1))

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AIHTTPClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    @staticmethod
    def _safe_json(response: httpx.Response) -> Any:
        try:
            return response.json()
        except Exception:
            return {}
