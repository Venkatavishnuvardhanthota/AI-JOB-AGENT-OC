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


class BambooHRATSProvider(BaseATSProvider):
    name = "bamboohr"
    display_name = "BambooHR"
    description = "BambooHR ATS job application adapter"
    version = "1.0.0"
    homepage_url = "https://www.bamboohr.com"
    requires_login = True

    url_patterns = [
        r"bamboohr\.com",
        r"\.bamboohr\.com",
    ]

    _capabilities = [
        ATSProviderCapability.JOB_SEARCH,
        ATSProviderCapability.JOB_DETAILS,
        ATSProviderCapability.APPLY,
        ATSProviderCapability.UPLOAD_RESUME,
        ATSProviderCapability.UPLOAD_COVER_LETTER,
        ATSProviderCapability.AUTO_FILL,
        ATSProviderCapability.LOGIN,
        ATSProviderCapability.DETECT,
        ATSProviderCapability.VALIDATE,
    ]

    def __init__(self, browser: BrowserService, config: Any | None = None) -> None:
        super().__init__(browser, config)
        self._subdomain = ""

    def login(self, page: Any, request: ATSLoginRequest) -> ATSLoginResult:
        if not request.email or not request.password:
            raise ATSLoginError("BambooHR login requires email and password.")
        subdomain = request.credentials.get("subdomain", "")
        if not subdomain:
            match = re.search(r"(https?://)?([^.]+)\.bamboohr\.com", self.browser.get_url(page) if page else "")
            subdomain = match.group(2) if match else ""
        if not subdomain:
            raise ATSLoginError("BambooHR subdomain is required.")
        self._subdomain = subdomain
        try:
            login_url = f"https://{subdomain}.bamboohr.com/login.php"
            self.browser.navigate(page, login_url)
            self.browser.safe_fill(page, 'input[name="username"], input[type="email"]', request.email)
            self.browser.safe_fill(page, 'input[name="password"], input[type="password"]', request.password)
            self.browser.safe_click(page, 'button[type="submit"], input[type="submit"]')
            self.browser.wait_for_network_idle(page)
            return ATSLoginResult(success=True, message="BambooHR login successful.")
        except Exception as e:
            raise ATSLoginError(f"BambooHR login failed: {e}") from e

    def find_job(self, page: Any, request: ATSJobSearchRequest) -> list[ATSJobInfo]:
        jobs: list[ATSJobInfo] = []
        try:
            careers_url = f"https://{self._subdomain}.bamboohr.com/careers"
            self.browser.navigate(page, careers_url)
            self.browser.wait_for_selector(page, ".job-listing, [data-job-id], .job-title, a[href*='careers']")
            links = self.browser.query_selector_all(
                page, ".job-listing a, [data-job-id] a, .job-title a, a[href*='/careers/']"
            )
            seen = set()
            for link in links:
                href = self.browser.get_attribute(link, "href") or ""
                if href in seen:
                    continue
                seen.add(href)
                title = self.browser.get_text_content(link) or "Untitled"
                full_url = href if href.startswith("http") else f"https://{self._subdomain}.bamboohr.com{href}"
                jobs.append(
                    ATSJobInfo(
                        provider_job_id=self._extract_job_id(full_url),
                        title=title.strip(),
                        url=full_url,
                        apply_url=full_url,
                    )
                )
        except Exception as e:
            self._logger.warning("BambooHR job search failed", error=str(e))
        return jobs

    def open_application(self, page: Any, request: ATSApplicationRequest) -> ATSApplicationResult:
        try:
            self.browser.navigate(page, request.job_url)
            self.browser.safe_click(page, "button:has-text('Apply'), a:has-text('Apply Now')")
            self.browser.wait_for_network_idle(page)
            if request.resume_path:
                self.browser.upload_file(page, 'input[type="file"]', request.resume_path)
            if request.fields:
                for selector, value in request.fields.items():
                    if self.browser.is_visible(page, selector):
                        self.browser.safe_fill(page, selector, value)
            return ATSApplicationResult(
                success=True,
                message="BambooHR application page opened successfully.",
            )
        except Exception as e:
            return ATSApplicationResult(
                success=False,
                errors=[str(e)],
            )

    def validate(self, page: Any) -> ATSValidationResult:
        result = ATSValidationResult(valid=True, provider_name=self.name)
        bamboohr_indicators = [
            "bamboohr.com",
            "bamboohr",
        ]
        for indicator in bamboohr_indicators:
            found = indicator in (self.browser.get_url(page) if page else "")
            result.detected_elements[indicator] = found
        if not any(result.detected_elements.values()):
            result.valid = False
            result.errors.append("No BambooHR indicators found on the page.")
        return result

    @staticmethod
    def _extract_job_id(url: str) -> str:
        match = re.search(r"/careers/(\d+)", url)
        return match.group(1) if match else url.split("/")[-1].split("?")[0] if url else ""
