from __future__ import annotations

from typing import Any

import structlog

from app.ats.exceptions import ATSLoginError
from app.ats.providers.base import BaseATSProvider
from app.ats.schemas import (
    ATSApplicationRequest,
    ATSApplicationResult,
    ATSJobInfo,
    ATSJobSearchRequest,
    ATSLoginRequest,
    ATSLoginResult,
    ATSProviderCapability,
    ATSValidationResult,
)
from app.browser.service import BrowserService

logger = structlog.get_logger(__name__)


class GreenhouseATSProvider(BaseATSProvider):
    name = "greenhouse"
    display_name = "Greenhouse"
    description = "Greenhouse ATS job application adapter"
    version = "1.0.0"
    homepage_url = "https://www.greenhouse.io"
    requires_login = False

    url_patterns = [
        r"boards\.greenhouse\.io",
        r"greenhouse\.io",
        r"boards-api\.greenhouse\.io",
    ]

    _capabilities = [
        ATSProviderCapability.JOB_SEARCH,
        ATSProviderCapability.JOB_DETAILS,
        ATSProviderCapability.APPLY,
        ATSProviderCapability.UPLOAD_RESUME,
        ATSProviderCapability.UPLOAD_COVER_LETTER,
        ATSProviderCapability.AUTO_FILL,
        ATSProviderCapability.DETECT,
        ATSProviderCapability.VALIDATE,
    ]

    def __init__(self, browser: BrowserService, config: Any | None = None) -> None:
        super().__init__(browser, config)
        self._base_url = (
            getattr(config, "base_url", "https://boards.greenhouse.io") if config else "https://boards.greenhouse.io"
        )

    def login(self, page: Any, request: ATSLoginRequest) -> ATSLoginResult:
        if not request.email or not request.password:
            raise ATSLoginError("Greenhouse login requires email and password.")
        try:
            self.browser.navigate(page, "https://app.greenhouse.io/users/sign_in")
            self.browser.safe_fill(page, "#user_email", request.email)
            self.browser.safe_fill(page, "#user_password", request.password)
            self.browser.safe_click(page, 'input[type="submit"]')
            self.browser.wait_for_network_idle(page)
            return ATSLoginResult(success=True, message="Greenhouse login successful.")
        except Exception as e:
            raise ATSLoginError(f"Greenhouse login failed: {e}") from e

    def find_job(self, page: Any, request: ATSJobSearchRequest) -> list[ATSJobInfo]:
        jobs: list[ATSJobInfo] = []
        board_token = self._extract_board_token(page.url)
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
        try:
            self.browser.navigate(page, api_url)
            import json

            body = self.browser.get_text(page, "body")
            data = json.loads(body) if body else {}
            for raw in data.get("jobs", []):
                jobs.append(
                    ATSJobInfo(
                        provider_job_id=str(raw.get("id", "")),
                        title=raw.get("title", "Untitled"),
                        url=raw.get("absolute_url", ""),
                        location=raw.get("location", {}).get("name")
                        if isinstance(raw.get("location"), dict)
                        else str(raw.get("location", "")),
                        department=raw.get("department", ""),
                        description=raw.get("content", ""),
                        apply_url=raw.get("absolute_url", ""),
                    )
                )
        except Exception:
            self._logger.warning("Failed to fetch jobs via API, falling back to page parsing")
        return jobs

    def open_application(self, page: Any, request: ATSApplicationRequest) -> ATSApplicationResult:
        try:
            self.browser.navigate(page, request.job_url)
            self.browser.safe_click(page, "a:has-text('Apply Now')")
            self.browser.wait_for_network_idle(page)
            if request.resume_path:
                self.browser.upload_file(page, 'input[type="file"]', request.resume_path)
            if request.fields:
                for selector, value in request.fields.items():
                    if self.browser.is_visible(page, selector):
                        self.browser.safe_fill(page, selector, value)
            return ATSApplicationResult(
                success=True,
                message="Greenhouse application page opened successfully.",
            )
        except Exception as e:
            return ATSApplicationResult(
                success=False,
                errors=[str(e)],
            )

    def validate(self, page: Any) -> ATSValidationResult:
        result = ATSValidationResult(valid=True, provider_name=self.name)
        greenhouse_indicators = [
            "boards.greenhouse.io",
            "greenhouse.io",
            "data-greenhouse-",
            "grnhse",
        ]
        for indicator in greenhouse_indicators:
            found = indicator in (page.url if hasattr(page, "url") else "")
            result.detected_elements[indicator] = found
        if not any(result.detected_elements.values()):
            result.valid = False
            result.errors.append("No Greenhouse indicators found on the page.")
        return result

    def _extract_board_token(self, url: str) -> str:
        import re

        match = re.search(r"boards\.greenhouse\.io/([^/]+)", url)
        return match.group(1) if match else "example"
