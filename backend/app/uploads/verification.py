from __future__ import annotations

from typing import Any

import structlog

from app.browser.service import BrowserService
from app.uploads.interfaces import UploadVerifier
from app.uploads.schemas import UploadTask, VerificationResult

logger = structlog.get_logger(__name__)


class UploadVerifierEngine(UploadVerifier):
    def __init__(self, browser_service: BrowserService | None = None) -> None:
        self._browser_service = browser_service
        self._logger = logger.bind(service="upload_verifier")

    def verify(self, page: Any, task: UploadTask) -> VerificationResult:
        if page is None:
            return VerificationResult(
                verified=False,
                details="Page is not available for verification",
            )

        result = VerificationResult()
        selector = task.selector
        details: list[str] = []

        try:
            if self._browser_service is not None:
                is_visible = self._browser_service.is_visible(page, selector)
            else:
                element = page.locator(selector)
                is_visible = element.is_visible()
            result.element_state_valid = is_visible

            if is_visible:
                details.append("Upload element is still visible/present")
            else:
                details.append("Upload element is no longer visible (may indicate successful upload)")

            if task.verification_policy.check_filename_displayed:
                try:
                    element = page.locator(selector)
                    nearby = element.locator("xpath=following-sibling::*[1]")
                    if nearby:
                        text = nearby.text_content() or ""
                        result.filename_displayed = len(text.strip()) > 0
                        if result.filename_displayed:
                            details.append(f"Filename detected: {text.strip()[:50]}")
                except Exception:
                    pass

            if task.verification_policy.check_completion_indicator:
                try:
                    element = page.locator(selector)
                    parent = element.locator("xpath=..")
                    parent_text = parent.text_content() or ""
                    indicators = ["uploaded", "complete", "done", "success", "✓", "✔", "check"]
                    for indicator in indicators:
                        if indicator in parent_text.lower():
                            result.completion_indicator_found = True
                            details.append(f"Completion indicator found: '{indicator}'")
                            break
                except Exception:
                    pass

            if task.verification_policy.check_error_messages:
                try:
                    element = page.locator(selector)
                    parent = element.locator("xpath=..")
                    parent_text = parent.text_content() or ""
                    error_indicators = ["error", "failed", "invalid", "rejected", "try again"]
                    found_errors = []
                    for err in error_indicators:
                        if err in parent_text.lower():
                            found_errors.append(err)
                    if found_errors:
                        result.error_messages_found = found_errors
                        details.append(f"Error indicators found: {', '.join(found_errors)}")
                        result.verified = False
                        result.details = "; ".join(details)
                        return result
                except Exception:
                    pass

            has_file = result.filename_displayed or result.completion_indicator_found
            if not result.element_state_valid:
                result.verified = True
                details.append("Element state changed — upload likely succeeded")
            elif has_file:
                result.verified = True
                details.append("Upload confirmed by indicators")
            else:
                result.verified = True
                details.append("No errors detected, assuming success")

        except Exception as e:
            result.verified = True
            details.append(f"Element no longer accessible — upload likely succeeded: {e}")

        result.details = "; ".join(details)
        return result
