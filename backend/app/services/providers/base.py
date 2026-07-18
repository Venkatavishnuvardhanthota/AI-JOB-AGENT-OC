import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.services.providers.config import PROVIDER_CONFIGS, ProviderSettings
from app.services.providers.errors import ProviderError
from app.services.providers.logging import ProviderLogger
from app.services.providers.metrics import get_metrics_collector
from app.services.providers.request_manager import RequestManager


@dataclass
class RawJobData:
    """Normalized raw job data returned by every provider."""

    title: str
    company_name: str
    description: str | None = None
    location: str | None = None
    url: str | None = None
    source_job_id: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    salary_period: str | None = None
    posted_at: datetime | None = None
    job_type: str | None = None
    remote: bool = False
    apply_url: str | None = None
    company_url: str | None = None
    company_logo_url: str | None = None
    skills: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    benefits: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    raw: dict[str, Any] | None = None


class BaseProvider(ABC):
    """Abstract base class for all job providers."""

    def __init__(self, settings: ProviderSettings | None = None) -> None:
        self.settings = settings or PROVIDER_CONFIGS.get(self.name)
        if self.settings is None:
            raise ProviderError(f"No configuration found for provider '{self.name}'")
        self._request_manager = RequestManager(self.name, self.settings)
        self._log = ProviderLogger(self.name)
        self._metrics = get_metrics_collector()

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider identifier."""

    @property
    def enabled(self) -> bool:
        return self.settings.enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self.settings.enabled = value

    @abstractmethod
    async def search(self, query: str, **kwargs) -> list[RawJobData]:
        """Search for jobs matching the query."""

    async def _request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        json_data: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        """Make a rate-limited HTTP request via the RequestManager."""
        start = time.monotonic()
        try:
            response = await self._request_manager.request(
                method=method, url=url, headers=headers,
                params=params, json_data=json_data, timeout=timeout,
            )
            elapsed = (time.monotonic() - start) * 1000
            self._metrics.record_request(self.name, success=True, duration_ms=elapsed)
            self._log.request_summary(method, url, response.status_code, elapsed)
            return response
        except Exception:
            elapsed = (time.monotonic() - start) * 1000
            self._metrics.record_request(self.name, success=False, duration_ms=elapsed)
            raise

    async def _get_json(self, url: str, **kwargs) -> Any:
        """GET a URL and parse JSON response."""
        return await self._request_manager.get_json(url, **kwargs)

    async def _get_html(self, url: str, **kwargs) -> str:
        """GET a URL and return the HTML text."""
        return await self._request_manager.get_html(url, **kwargs)

    async def close(self) -> None:
        await self._request_manager.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
