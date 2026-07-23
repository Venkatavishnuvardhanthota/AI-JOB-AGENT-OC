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


class LeverATSProvider(BaseATSProvider):
    name = "lever"
    display_name = "Lever"
    description = "Lever ATS job application adapter"
    version = "1.0.0"
    homepage_url = "https://www.lever.co"
    requires_login = False

    url_patterns = [
        r"jobs\.lever\.co",
        r"lever\.co",
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
        self._base_url = getattr(config, "base_url", "https://jobs.lever.co") if config else "https://jobs.lever.co"

    def login(self, page: Any, request: ATSLoginRequest) -> ATSLoginResult:
        if not request.email or not request.password:
            raise ATSLoginError("Lever login requires email and password.")
        try:
            self.browser.navigate(page, "https://auth.lever.co/login")
            self.browser.safe_fill(page, 'input[name="email"]', request.email)
            self.browser.safe_fill(page, 'input[name="password"]', request.password)
            self.browser.safe_click(page, 'button[type="submit"]')
            self.browser.wait_for_network_idle(page)
            return ATSLoginResult(success=True, message="Lever login successful.")
        except Exception as e:
            raise ATSLoginError(f"Lever login failed: {e}") from e

    def find_job(self, page: Any, request: ATSJobSearchRequest) -> list[ATSJobInfo]:
        jobs: list[ATSJobInfo] = []
        try:
            self.browser.navigate(page, self._base_url)
            self.browser.wait_for_selector(page, ".posting, .job-posting, [data-job-id]")
            job_cards = self._get_job_card_elements(page)
            for card in job_cards:
                title_el = card.query_selector("a, h2, h3")
                if title_el:
                    title = title_el.text_content() or "Untitled"
                    url = title_el.get_attribute("href") or ""
                    if url and not url.startswith("http"):
                        url = self._base_url + url
                    jobs.append(
                        ATSJobInfo(
                            provider_job_id=self._extract_job_id(url),
                            title=title.strip(),
                            url=url,
                            apply_url=url,
                        )
                    )
        except Exception as e:
            self._logger.warning("Lever job search failed", error=str(e))
        return jobs

    def open_application(self, page: Any, request: ATSApplicationRequest) -> ATSApplicationResult:
        try:
            self.browser.navigate(page, request.job_url)
            self.browser.safe_click(page, "a:has-text('Apply'), button:has-text('Apply')")
            self.browser.wait_for_network_idle(page)
            if request.resume_path:
                self.browser.upload_file(page, 'input[type="file"]', request.resume_path)
            if request.fields:
                for selector, value in request.fields.items():
                    if self.browser.is_visible(page, selector):
                        self.browser.safe_fill(page, selector, value)
            return ATSApplicationResult(
                success=True,
                message="Lever application page opened successfully.",
            )
        except Exception as e:
            return ATSApplicationResult(
                success=False,
                errors=[str(e)],
            )

    def validate(self, page: Any) -> ATSValidationResult:
        result = ATSValidationResult(valid=True, provider_name=self.name)
        lever_indicators = [
            "jobs.lever.co",
            "lever.co",
            "lever-",
        ]
        for indicator in lever_indicators:
            found = indicator in (page.url if hasattr(page, "url") else "")
            result.detected_elements[indicator] = found
        if not any(result.detected_elements.values()):
            result.valid = False
            result.errors.append("No Lever indicators found on the page.")
        return result

    def _get_job_card_elements(self, page: Any) -> list[Any]:
        try:
            return page.query_selector_all(".posting, .job-posting, [data-job-id]")
        except Exception:
            return []

    @staticmethod
    def _extract_job_id(url: str) -> str:
        import re

        match = re.search(r"lever\.co/[^/]+/([^?/]+)", url)
        return match.group(1) if match else url.split("/")[-1] if url else ""
