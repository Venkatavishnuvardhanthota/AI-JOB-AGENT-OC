"""Standalone HTTP Request Manager for provider API calls."""

import logging
from typing import Any

import httpx

from app.services.providers.config import DEFAULT_USER_AGENT, ProviderSettings
from app.services.providers.errors import (
    ProviderError,
    ProviderParseError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from app.services.providers.rate_limiter import RateLimiterRegistry

logger = logging.getLogger(__name__)


class RequestManager:
    """Manages HTTP requests to provider APIs with rate limiting, auth, and error handling.

    Extracted from BaseProvider for reuse and standalone testing.
    """

    def __init__(
        self,
        provider_name: str,
        settings: ProviderSettings,
        rate_limiter_registry: RateLimiterRegistry | None = None,
    ) -> None:
        self.provider_name = provider_name
        self.settings = settings
        self._rate_limiter_registry = rate_limiter_registry or RateLimiterRegistry()
        self._client: httpx.AsyncClient | None = None

    async def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        json_data: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Make a rate-limited HTTP request with auth, retry headers, and error mapping."""
        await self._acquire_rate_limit()

        request_headers = self._build_headers(headers)
        merged_params = self._build_params(params)

        client = await self._get_client()
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=request_headers,
                params=merged_params or None,
                json=json_data,
                timeout=timeout or self.settings.timeout_seconds,
                follow_redirects=True,
            )
        except httpx.TimeoutException as e:
            raise ProviderTimeoutError(
                str(e), provider=self.provider_name, timeout=self.settings.timeout_seconds,
            ) from e
        except httpx.HTTPError as e:
            raise ProviderUnavailableError(str(e), provider=self.provider_name) from e

        self._check_response_errors(response)
        return response

    async def get_json(self, url: str, **kwargs) -> Any:
        """GET and parse JSON response."""
        response = await self.request("GET", url, **kwargs)
        try:
            return response.json()
        except ValueError as e:
            raise ProviderParseError(
                f"Invalid JSON: {e}", provider=self.provider_name, raw=response.text[:500],
            ) from e

    async def get_html(self, url: str, **kwargs) -> str:
        """GET and return response text."""
        response = await self.request("GET", url, **kwargs)
        return response.text

    async def _acquire_rate_limit(self) -> None:
        limiter = self._rate_limiter_registry.get(
            self.provider_name,
            rate=self.settings.requests_per_second,
        )
        await limiter.acquire()

    def _build_headers(self, extra: dict[str, str] | None) -> dict[str, str]:
        headers = {
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "text/html,application/json,*/*",
            "Accept-Language": "en-US,en;q=0.9",
        }
        if extra:
            headers.update(extra)
        headers.update(self.settings.extra_headers)
        if self.settings.api_key:
            headers.setdefault("Authorization", f"Bearer {self.settings.api_key}")
        return headers

    def _build_params(self, extra: dict[str, str] | None) -> dict[str, str]:
        params = dict(self.settings.extra_params)
        if extra:
            params.update(extra)
        return params

    def _check_response_errors(self, response: httpx.Response) -> None:
        if response.status_code == 429:
            retry_after = float(response.headers.get("Retry-After", "5"))
            raise ProviderRateLimitError(
                f"HTTP 429: {response.text[:200]}",
                provider=self.provider_name,
                retry_after=retry_after,
            )
        if response.status_code == 401:
            raise ProviderError(f"HTTP 401 Unauthorized for {self.provider_name}")
        if response.status_code == 403:
            raise ProviderError(f"HTTP 403 Forbidden for {self.provider_name}")
        if response.status_code >= 500:
            raise ProviderUnavailableError(
                f"HTTP {response.status_code} from {self.provider_name}: {response.text[:200]}",
                provider=self.provider_name,
            )
        response.raise_for_status()

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient()
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
