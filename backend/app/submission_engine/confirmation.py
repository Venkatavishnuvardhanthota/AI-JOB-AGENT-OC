from __future__ import annotations

import time
from typing import Any

import structlog

from app.submission_engine.exceptions import SubmissionConfirmationError
from app.submission_engine.interfaces import SubmissionConfirmer
from app.submission_engine.schemas import ConfirmationResult

logger = structlog.get_logger(__name__)


class SubmissionConfirmerEngine(SubmissionConfirmer):
    def __init__(self) -> None:
        self._logger = logger.bind(service="submission_confirmer")

    def confirm(self, page: Any, timeout_ms: float) -> ConfirmationResult:
        if page is None:
            return ConfirmationResult(details="Page is not available")

        result = ConfirmationResult()
        start = time.time()

        try:
            while (time.time() - start) * 1000 < timeout_ms:
                current_url = page.url
                if current_url and current_url != "about:blank":
                    result.redirect_url = current_url
                    break
                __import__("time").sleep(0.5)

            body = page.text_content("body") or ""
            import re

            confirm_patterns = [
                (r"application\s*(?:has been)?\s*submitted", "success_page_detected"),
                (r"thank\s*you\s*(?:for)?\s*(?:your)?\s*application", "success_page_detected"),
                (r"(?:application|confirmation)\s*(?:ID|#|number)[:\s]*([A-Z0-9-]+)", "id_or_number"),
                (r"submission\s*(?:ID|#|number)[:\s]*([A-Z0-9-]+)", "id_or_number"),
                (r"successfully\s*submitted", "success_page_detected"),
            ]

            for pattern, match_type in confirm_patterns:
                match = re.search(pattern, body, re.IGNORECASE)
                if match:
                    result.success_page_detected = True
                    result.provider_acknowledged = True
                    if match_type == "id_or_number" and match.groups():
                        captured = match.group(1)
                        if (
                            re.search(r"confirmation", pattern, re.IGNORECASE)
                            or "confirmation" in str(match.string).lower()
                        ):
                            result.confirmation_number = captured
                        else:
                            result.application_id = captured
                    break

            dupe_patterns = [
                r"already\s*(?:applied|submitted)",
                r"duplicate\s*application",
                r"you\s*have\s*already",
            ]
            for pattern in dupe_patterns:
                if re.search(pattern, body, re.IGNORECASE):
                    result.duplicate_detected = True
                    break

            if result.success_page_detected:
                result.confirmed = True
                result.details = "Confirmation page detected"
            elif result.duplicate_detected:
                result.details = "Duplicate submission detected"
            elif result.redirect_url:
                result.confirmed = True
                result.details = f"Redirect detected: {result.redirect_url}"
            else:
                result.details = "No confirmation detected"

        except Exception as e:
            raise SubmissionConfirmationError(f"Confirmation check failed: {e}") from e

        return result
