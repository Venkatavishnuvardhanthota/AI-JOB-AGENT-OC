from __future__ import annotations

from typing import Any

import structlog

from app.ats.config import ATSConfig
from app.ats.exceptions import ATSNotSupportedError
from app.ats.factory import ATSProviderFactory
from app.ats.registry import ATSProviderRegistry
from app.ats.schemas import (
    ATSApplicationRequest,
    ATSApplicationResult,
    ATSDetectionResult,
    ATSJobInfo,
    ATSJobSearchRequest,
    ATSLoginRequest,
    ATSLoginResult,
    ATSNavigationRequest,
    ATSNavigationResult,
    ATSProviderInfo,
    ATSProviderMetadata,
    ATSValidationResult,
)
from app.browser.service import BrowserService

logger = structlog.get_logger(__name__)


class ATSService:
    def __init__(
        self,
        registry: ATSProviderRegistry,
        factory: ATSProviderFactory,
        config: ATSConfig,
        browser: BrowserService,
    ) -> None:
        self._registry = registry
        self._factory = factory
        self._config = config
        self._browser = browser
        self._logger = logger.bind(service="ats")

    def detect(self, url: str) -> ATSDetectionResult | None:
        return self._registry.detect_result(url)

    def get_provider(self, name: str) -> Any:
        return self._registry.resolve(name)

    def get_provider_for_url(self, url: str) -> Any | None:
        return self._registry.detect(url)

    def supports(self, url: str) -> bool:
        return self._registry.detect(url) is not None

    def list_providers(self) -> list[dict[str, Any]]:
        return self._registry.list_details()

    def login(self, provider_name: str, request: ATSLoginRequest) -> ATSLoginResult:
        provider = self._registry.resolve(provider_name)
        return provider.login(None, request)

    def navigate(
        self,
        provider_name: str,
        request: ATSNavigationRequest,
    ) -> ATSNavigationResult:
        provider = self._registry.resolve(provider_name)
        return provider.navigate(None, request)

    def find_jobs(
        self,
        provider_name: str,
        request: ATSJobSearchRequest,
    ) -> list[ATSJobInfo]:
        provider = self._registry.resolve(provider_name)
        return provider.find_job(None, request)

    def find_jobs_by_url(
        self,
        url: str,
        request: ATSJobSearchRequest,
    ) -> list[ATSJobInfo]:
        provider = self._registry.detect(url)
        if provider is None:
            raise ATSNotSupportedError(f"No ATS provider supports URL: {url}")
        return self.find_jobs(provider.name, request)

    def open_application(
        self,
        provider_name: str,
        request: ATSApplicationRequest,
    ) -> ATSApplicationResult:
        provider = self._registry.resolve(provider_name)
        return provider.open_application(None, request)

    def validate(self, provider_name: str) -> ATSValidationResult:
        provider = self._registry.resolve(provider_name)
        return provider.validate(None)

    def get_provider_metadata(self, provider_name: str) -> ATSProviderMetadata:
        provider = self._registry.resolve(provider_name)
        return provider.metadata()

    def get_provider_info(self, provider_name: str) -> ATSProviderInfo:
        provider = self._registry.resolve(provider_name)
        meta = provider.metadata()
        return ATSProviderInfo(
            name=meta.name,
            display_name=meta.display_name,
            description=meta.description,
            version=meta.version,
            homepage_url=meta.homepage_url,
            capabilities=[c.value for c in meta.capabilities],
            url_patterns=meta.url_patterns,
            requires_auth=meta.requires_auth,
            requires_login=meta.requires_login,
        )
