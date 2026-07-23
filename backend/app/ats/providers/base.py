from __future__ import annotations

import re
from typing import Any

import structlog

from app.ats.exceptions import (
    ATSNavigationError,
    ATSNotSupportedError,
)
from app.ats.interfaces import ATSProvider
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
    ATSProviderCapability,
    ATSProviderMetadata,
    ATSValidationResult,
)
from app.browser.service import BrowserService

logger = structlog.get_logger(__name__)


class BaseATSProvider(ATSProvider):
    name: str = ""
    display_name: str = ""
    description: str = ""
    version: str = "0.1.0"
    homepage_url: str = ""
    requires_auth: bool = False
    requires_login: bool = False

    url_patterns: list[str] = []
    _capabilities: list[ATSProviderCapability] = []

    def __init__(self, browser: BrowserService, config: Any | None = None) -> None:
        super().__init__(browser, config)
        self._logger = logger.bind(provider=self.name)

    def supports(self, url: str) -> bool:
        return any(re.search(pattern, url) for pattern in self.url_patterns)

    def detect(self, url: str) -> ATSDetectionResult | None:
        for pattern in self.url_patterns:
            match = re.search(pattern, url)
            if match:
                return ATSDetectionResult(
                    provider_name=self.name,
                    provider_display_name=self.display_name,
                    confidence=0.95,
                    matched_pattern=pattern,
                    url=url,
                )
        return None

    def login(self, page: Any, request: ATSLoginRequest) -> ATSLoginResult:
        if not self.requires_login:
            return ATSLoginResult(success=True, message=f"{self.display_name} does not require login.")
        raise ATSNotSupportedError(f"Login not implemented for {self.display_name}")

    def navigate(self, page: Any, request: ATSNavigationRequest) -> ATSNavigationResult:
        try:
            result = self.browser.navigate(page, request.url, request.timeout_ms, request.wait_until)
            if request.wait_for_selector:
                self.browser.wait_for_selector(page, request.wait_for_selector)
            return ATSNavigationResult(
                success=result.success,
                url=result.url,
                title=result.title,
                duration_ms=result.duration_ms,
                error=result.error,
            )
        except Exception as e:
            raise ATSNavigationError(f"Navigation to {request.url} failed: {e}") from e

    def find_job(self, page: Any, request: ATSJobSearchRequest) -> list[ATSJobInfo]:
        raise ATSNotSupportedError(f"Job search not implemented for {self.display_name}")

    def open_application(self, page: Any, request: ATSApplicationRequest) -> ATSApplicationResult:
        raise ATSNotSupportedError(f"Application not implemented for {self.display_name}")

    def validate(self, page: Any) -> ATSValidationResult:
        return ATSValidationResult(
            valid=True,
            provider_name=self.name,
        )

    def capabilities(self) -> list[ATSProviderCapability]:
        return self._capabilities

    def metadata(self) -> ATSProviderMetadata:
        return ATSProviderMetadata(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            version=self.version,
            homepage_url=self.homepage_url,
            capabilities=self._capabilities,
            url_patterns=self.url_patterns,
            requires_auth=self.requires_auth,
            requires_login=self.requires_login,
        )

    def _click_and_wait(self, page: Any, selector: str, timeout_ms: float | None = None) -> None:
        self.browser.safe_click(page, selector, timeout_ms)

    def _fill_and_wait(self, page: Any, selector: str, value: str, timeout_ms: float | None = None) -> None:
        self.browser.safe_fill(page, selector, value, timeout_ms)

    def _wait_and_get_text(self, page: Any, selector: str) -> str:
        return self.browser.get_text(page, selector)

    def _is_element_present(self, page: Any, selector: str) -> bool:
        return self.browser.is_visible(page, selector)

    def _take_screenshot(self, page: Any, name: str | None = None) -> str:
        return self.browser.take_screenshot(page, name)

    def _take_failure_screenshot(self, page: Any, context: str = "ats_failure") -> str:
        return self.browser.take_failure_screenshot(page, context)
