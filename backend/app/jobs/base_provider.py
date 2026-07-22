from __future__ import annotations

from abc import abstractmethod

import structlog

from app.jobs.config import JobDiscoveryConfig
from app.jobs.http_client import JobHTTPClient
from app.jobs.interfaces import JobProvider
from app.jobs.rate_limiter import TokenBucketRateLimiter
from app.jobs.schemas import (
    JobProviderInfo,
    JobSearchRequest,
    JobSearchResponse,
)

logger = structlog.get_logger(__name__)


class BaseJobProvider(JobProvider):
    name: str = ""
    display_name: str = ""
    description: str = ""
    version: str = "0.1.0"
    supports_pagination: bool = True
    supports_filters: bool = False

    base_url: str = ""
    api_key_header: str = "Authorization"
    api_key_scheme: str = "Bearer"
    page_size: int = 20
    rate_limit_rate: float = 10.0
    rate_limit_burst: int = 5

    def __init__(self, config: JobDiscoveryConfig) -> None:
        super().__init__(config)
        self._client = self._build_client()

    def _build_client(self) -> JobHTTPClient:
        api_key = self._resolve_api_key()
        rate_limiter = None
        if self.rate_limit_rate > 0:
            rate_limiter = TokenBucketRateLimiter(
                rate=self.rate_limit_rate,
                burst=self.rate_limit_burst,
            )
        return JobHTTPClient(
            base_url=self.base_url,
            timeout_seconds=self.config.request_timeout_seconds,
            max_retries=self.config.retry_count,
            api_key=api_key,
            api_key_header=self.api_key_header,
            api_key_scheme=self.api_key_scheme,
            default_params=self._default_query_params(),
            rate_limiter=rate_limiter,
        )

    def _resolve_api_key(self) -> str | None:
        return None

    def _default_query_params(self) -> dict[str, str]:
        return {}

    @abstractmethod
    async def search_jobs(self, request: JobSearchRequest) -> JobSearchResponse:
        ...

    async def health_check(self) -> bool:
        try:
            info = await self._fetch_provider_status()
            return bool(info)
        except Exception:
            logger.exception("Health check failed", provider=self.name)
            return False

    async def provider_info(self) -> JobProviderInfo:
        is_healthy = await self.health_check()
        return JobProviderInfo(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            is_available=is_healthy,
            supports_pagination=self.supports_pagination,
            supports_filters=self.supports_filters,
            version=self.version,
        )

    async def _fetch_provider_status(self) -> object:
        return True

    def _build_search_url(self, request: JobSearchRequest) -> str:
        return ""

    def _build_search_params(self, request: JobSearchRequest) -> dict:
        return {}

    def _parse_response(self, data: dict, request: JobSearchRequest) -> JobSearchResponse:
        return JobSearchResponse()

    def _page_limit(self, request: JobSearchRequest) -> int:
        return min(request.limit, self.config.default_search_limit)

    def _page_offset(self, request: JobSearchRequest) -> int:
        return request.offset
