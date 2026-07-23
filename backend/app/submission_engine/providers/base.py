from __future__ import annotations

from typing import Any

from app.submission_engine.interfaces import SubmissionProvider
from app.submission_engine.schemas import ConfirmationResult


class BaseSubmissionProvider(SubmissionProvider):
    def __init__(self, name: str = "default") -> None:
        self._name = name

    def supports(self, url: str) -> bool:
        return True

    def submit(self, page: Any, timeout_ms: float) -> bool:
        if page is None:
            return False
        try:
            submit_btn = page.locator(
                "button[type='submit'], input[type='submit'], "
                "button:has-text('Submit'), button:has-text('Apply')"
            )
            if submit_btn and submit_btn.is_visible():
                submit_btn.click(timeout=timeout_ms)
                return True
            return False
        except Exception:
            return False

    def confirm(self, page: Any, timeout_ms: float) -> ConfirmationResult:
        result = ConfirmationResult()
        if page is None:
            return result

        try:
            current_url = page.url
            if current_url:
                result.redirect_url = current_url

            body = page.text_content("body") or ""

            import re
            confirm_patterns = [
                r"application\s*(?:has been)?\s*submitted",
                r"thank\s*you\s*(?:for)?\s*(?:your)?\s*application",
                r"application\s*(?:ID|#|number)[:\s]*([A-Z0-9-]+)",
                r"confirmation\s*(?:ID|#|number)[:\s]*([A-Z0-9-]+)",
                r"submission\s*(?:ID|#|number)[:\s]*([A-Z0-9-]+)",
                r"successfully\s*submitted",
            ]

            for pattern in confirm_patterns:
                match = re.search(pattern, body, re.IGNORECASE)
                if match:
                    result.success_page_detected = True
                    result.provider_acknowledged = True
                    if match.lastgroup or len(match.groups()) > 0:
                        captured = match.group(1) if match.groups() else None
                        if captured:
                            if "confirmation" in pattern or "Confirmation" in pattern:
                                result.confirmation_number = captured
                            elif "application" in pattern or "Application" in pattern:
                                result.application_id = captured
                    break

            duplicate_patterns = [
                r"already\s*(?:applied|submitted)",
                r"duplicate\s*application",
                r"you\s*have\s*already",
            ]
            for pattern in duplicate_patterns:
                if re.search(pattern, body, re.IGNORECASE):
                    result.duplicate_detected = True
                    break

            if result.success_page_detected:
                result.confirmed = True
                result.details = "Confirmation page detected"
            elif result.duplicate_detected:
                result.details = "Duplicate submission detected"
            else:
                result.details = "No confirmation detected"

        except Exception:
            result.details = "Failed to check confirmation"

        return result

    @property
    def name(self) -> str:
        return self._name
