from __future__ import annotations

import re
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


class SmartRecruitersATSProvider(BaseATSProvider):
    name = "smartrecruiters"
    display_name = "SmartRecruiters"
    description = "SmartRecruiters ATS job application adapter"
    version = "1.0.0"
    homepage_url = "https://www.smartrecruiters.com"
    requires_login = False

    url_patterns = [
        r"jobs\.smartrecruiters\.com",
        r"smartrecruiters\.com",
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
            getattr(config, "base_url", "https://jobs.smartrecruiters.com")
            if config
            else "https://jobs.smartrecruiters.com"
        )

    def login(self, page: Any, request: ATSLoginRequest) -> ATSLoginResult:
        return ATSLoginResult(success=True, message="SmartRecruiters does not require login for job applications.")

    def find_job(self, page: Any, request: ATSJobSearchRequest) -> list[ATSJobInfo]:
        jobs: list[ATSJobInfo] = []
        try:
            self.browser.navigate(page, self._base_url)
            self.browser.wait_for_selector(page, ".job-listing, [data-job-id], .job-title")
            links = page.query_selector_all(
                ".job-listing a, [data-job-id] a, .job-title a, a[href*='jobs.smartrecruiters.com/']"
            )
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
            self._logger.warning("SmartRecruiters job search failed", error=str(e))
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
                message="SmartRecruiters application page opened successfully.",
            )
        except Exception as e:
            return ATSApplicationResult(
                success=False,
                errors=[str(e)],
            )

    def validate(self, page: Any) -> ATSValidationResult:
        result = ATSValidationResult(valid=True, provider_name=self.name)
        sr_indicators = [
            "jobs.smartrecruiters.com",
            "smartrecruiters.com",
            "smartrecruiters",
        ]
        for indicator in sr_indicators:
            found = indicator in (page.url if hasattr(page, "url") else "")
            result.detected_elements[indicator] = found
        if not any(result.detected_elements.values()):
            result.valid = False
            result.errors.append("No SmartRecruiters indicators found on the page.")
        return result

    @staticmethod
    def _extract_job_id(url: str) -> str:
        match = re.search(r"smartrecruiters\.com/(?:[^/]+/)+(\d+)", url)
        return match.group(1) if match else url.split("/")[-1].split("?")[0] if url else ""
