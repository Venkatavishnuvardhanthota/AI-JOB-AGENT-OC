from __future__ import annotations

import re
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


class WorkdayATSProvider(BaseATSProvider):
    name = "workday"
    display_name = "Workday"
    description = "Workday ATS job application adapter"
    version = "1.0.0"
    homepage_url = "https://www.workday.com"
    requires_login = False

    url_patterns = [
        r"myworkdayjobs\.com",
        r"workday\.com",
        r"wd5\.myworkdayjobs\.com",
        r"workdayjobs\.com",
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
            getattr(config, "base_url", "https://www.myworkdayjobs.com") if config else "https://www.myworkdayjobs.com"
        )

    def login(self, page: Any, request: ATSLoginRequest) -> ATSLoginResult:
        if not request.email or not request.password:
            raise ATSLoginError("Workday login requires email and password.")
        try:
            self.browser.safe_fill(page, 'input[type="email"], input[name="username"]', request.email)
            self.browser.safe_fill(page, 'input[type="password"], input[name="password"]', request.password)
            self.browser.safe_click(page, 'button[type="submit"]')
            self.browser.wait_for_network_idle(page)
            return ATSLoginResult(success=True, message="Workday login successful.")
        except Exception as e:
            raise ATSLoginError(f"Workday login failed: {e}") from e

    def find_job(self, page: Any, request: ATSJobSearchRequest) -> list[ATSJobInfo]:
        jobs: list[ATSJobInfo] = []
        try:
            if request.query:
                search_box = self.browser.query_selector(page, 'input[type="search"], input[placeholder*="Search"]')
                if search_box:
                    self.browser.element_fill(search_box, request.query)
                    self.browser.keyboard_press(page, "Enter")
                    self.browser.wait_for_network_idle(page)
            self.browser.wait_for_selector(page, "[data-automation-id*='job'], .job-listing, a[href*='job/']")
            links = self.browser.query_selector_all(
                page, "[data-automation-id*='job'] a, .job-listing a, a[href*='job/']"
            )
            seen = set()
            for link in links:
                href = self.browser.get_attribute(link, "href") or ""
                if href in seen:
                    continue
                seen.add(href)
                title = self.browser.get_text_content(link) or "Untitled"
                full_url = (
                    href
                    if href.startswith("http")
                    else f"https:{href}"
                    if href.startswith("//")
                    else f"{self._base_url}{href}"
                )
                jobs.append(
                    ATSJobInfo(
                        provider_job_id=self._extract_job_id(full_url),
                        title=title.strip(),
                        url=full_url,
                        apply_url=full_url,
                    )
                )
        except Exception as e:
            self._logger.warning("Workday job search failed", error=str(e))
        return jobs

    def open_application(self, page: Any, request: ATSApplicationRequest) -> ATSApplicationResult:
        try:
            self.browser.navigate(page, request.job_url)
            self.browser.safe_click(page, "button:has-text('Apply'), a:has-text('Apply')")
            self.browser.wait_for_network_idle(page)
            if request.resume_path:
                self.browser.upload_file(page, 'input[type="file"]', request.resume_path)
            if request.fields:
                for selector, value in request.fields.items():
                    if self.browser.is_visible(page, selector):
                        self.browser.safe_fill(page, selector, value)
            return ATSApplicationResult(
                success=True,
                message="Workday application page opened successfully.",
            )
        except Exception as e:
            return ATSApplicationResult(
                success=False,
                errors=[str(e)],
            )

    def validate(self, page: Any) -> ATSValidationResult:
        result = ATSValidationResult(valid=True, provider_name=self.name)
        workday_indicators = [
            "myworkdayjobs.com",
            "workday.com",
            "wd5.myworkdayjobs.com",
            "workdayjobs.com",
            "data-automation-id",
        ]
        for indicator in workday_indicators:
            found = indicator in (self.browser.get_url(page) if page else "") or self._check_page_source(
                page, indicator
            )
            result.detected_elements[indicator] = found
        if not any(result.detected_elements.values()):
            result.valid = False
            result.errors.append("No Workday indicators found on the page.")
        return result

    def _check_page_source(self, page: Any, text: str) -> bool:
        try:
            content = self.browser.get_content(page)
            return text in content
        except Exception:
            return False

    @staticmethod
    def _extract_job_id(url: str) -> str:
        match = re.search(r"job/([^/?]+)", url)
        return match.group(1) if match else url.split("/")[-1].split("?")[0] if url else ""
