from __future__ import annotations

from typing import Any

import structlog

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


class AshbyATSProvider(BaseATSProvider):
    name = "ashby"
    display_name = "Ashby"
    description = "Ashby ATS job application adapter"
    version = "1.0.0"
    homepage_url = "https://www.ashbyhq.com"
    requires_login = False

    url_patterns = [
        r"jobs\.ashbyhq\.com",
        r"ashbyhq\.com",
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
            getattr(config, "base_url", "https://jobs.ashbyhq.com") if config else "https://jobs.ashbyhq.com"
        )

    def login(self, page: Any, request: ATSLoginRequest) -> ATSLoginResult:
        return ATSLoginResult(success=True, message="Ashby does not require login for job applications.")

    def find_job(self, page: Any, request: ATSJobSearchRequest) -> list[ATSJobInfo]:
        jobs: list[ATSJobInfo] = []
        try:
            self.browser.navigate(page, self._base_url)
            self.browser.wait_for_selector(page, "a[href*='/jobs/'], [data-job-id]")
            links = page.query_selector_all("a[href*='/jobs/']")
            seen = set()
            for link in links:
                href = link.get_attribute("href") or ""
                if href in seen:
                    continue
                seen.add(href)
                title = link.text_content() or "Untitled"
                full_url = href if href.startswith("http") else f"{self._base_url}{href}"
                jobs.append(
                    ATSJobInfo(
                        provider_job_id=self._extract_job_id(full_url),
                        title=title.strip(),
                        url=full_url,
                        apply_url=full_url,
                    )
                )
        except Exception as e:
            self._logger.warning("Ashby job search failed", error=str(e))
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
                message="Ashby application page opened successfully.",
            )
        except Exception as e:
            return ATSApplicationResult(
                success=False,
                errors=[str(e)],
            )

    def validate(self, page: Any) -> ATSValidationResult:
        result = ATSValidationResult(valid=True, provider_name=self.name)
        ashby_indicators = [
            "jobs.ashbyhq.com",
            "ashbyhq.com",
            "ashby-",
        ]
        for indicator in ashby_indicators:
            found = indicator in (page.url if hasattr(page, "url") else "")
            result.detected_elements[indicator] = found
        if not any(result.detected_elements.values()):
            result.valid = False
            result.errors.append("No Ashby indicators found on the page.")
        return result

    @staticmethod
    def _extract_job_id(url: str) -> str:
        import re

        match = re.search(r"ashbyhq\.com/jobs/([^/?]+)", url)
        return match.group(1) if match else url.split("/")[-1].split("?")[0] if url else ""
