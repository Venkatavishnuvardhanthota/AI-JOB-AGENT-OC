from __future__ import annotations

import asyncio
from typing import Any

import httpx
import structlog

from app.jobs.exceptions import ProviderUnavailableError
from app.jobs.rate_limiter import TokenBucketRateLimiter

logger = structlog.get_logger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class JobHTTPClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: int = 30,
        max_retries: int = 2,
        api_key: str | None = None,
        api_key_header: str = "Authorization",
        api_key_scheme: str = "Bearer",
        default_params: dict[str, str] | None = None,
        default_headers: dict[str, str] | None = None,
        rate_limiter: TokenBucketRateLimiter | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._max_retries = max_retries
        self._rate_limiter = rate_limiter

        headers = dict(default_headers or {})
        if api_key:
            headers[api_key_header] = f"{api_key_scheme} {api_key}" if api_key_scheme else api_key
        self._default_params = dict(default_params or {})

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            timeout=httpx.Timeout(timeout_seconds),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
        )

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        retry_on: set[int] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        retry_codes = retry_on or RETRYABLE_STATUS_CODES
        all_params = {**self._default_params, **(params or {})}
        last_exception: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                if self._rate_limiter:
                    await self._rate_limiter.acquire()

                response = await self._client.get(path, params=all_params, headers=headers)

                if response.status_code == 429:
                    if attempt < self._max_retries:
                        wait = self._retry_after(response, attempt)
                        logger.warning(
                            "Rate limited, retrying",
                            path=path,
                            attempt=attempt,
                            wait=wait,
                        )
                        await asyncio.sleep(wait)
                        continue
                    raise ProviderUnavailableError(
                        f"Rate limited by provider. Retry after {self._retry_after(response, attempt)}s"
                    )

                if response.status_code in retry_codes and attempt < self._max_retries:
                    wait = self._retry_after(response, attempt)
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
                    raise ProviderUnavailableError("Authentication failed: invalid or missing API key")
                if response.status_code == 403:
                    raise ProviderUnavailableError("Access forbidden: API key may lack permissions")
                if response.status_code == 404:
                    raise ProviderUnavailableError(f"Resource not found: {path}")
                if response.status_code >= 500 and attempt == self._max_retries:
                    raise ProviderUnavailableError(f"Provider returned {response.status_code}: {response.text[:200]}")

                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException:
                last_exception = ProviderUnavailableError(f"Request timed out after {self._client.timeout.read}s")
                if attempt < self._max_retries:
                    wait = 2**attempt
                    logger.warning("Timeout, retrying", path=path, attempt=attempt, wait=wait)
                    await asyncio.sleep(wait)
                    continue

            except (httpx.ConnectError, httpx.RemoteProtocolError) as exc:
                last_exception = ProviderUnavailableError(f"Connection failed: {exc}")
                if attempt < self._max_retries:
                    wait = 2**attempt
                    logger.warning("Connection error, retrying", path=path, attempt=attempt, wait=wait)
                    await asyncio.sleep(wait)
                    continue

            except ProviderUnavailableError:
                raise

            except httpx.HTTPStatusError as exc:
                raise ProviderUnavailableError(f"HTTP {exc.response.status_code}: {exc.response.text[:200]}") from exc

            except Exception as exc:
                last_exception = ProviderUnavailableError(f"Unexpected error: {exc}")
                if attempt < self._max_retries:
                    await asyncio.sleep(2**attempt)
                    continue

        raise last_exception or ProviderUnavailableError("Request failed after all retries")

    def _retry_after(self, response: httpx.Response, attempt: int) -> float:
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return float(2**attempt)

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> JobHTTPClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
