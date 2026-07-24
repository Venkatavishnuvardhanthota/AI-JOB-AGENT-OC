from __future__ import annotations

from typing import Any

from app.submission_engine.confirmation import SubmissionConfirmerEngine
from app.submission_engine.interfaces import SubmissionProvider
from app.submission_engine.schemas import ConfirmationResult


class BaseSubmissionProvider(SubmissionProvider):
    def __init__(self, name: str = "default") -> None:
        self._name = name
        self._confirmer = SubmissionConfirmerEngine()

    def supports(self, url: str) -> bool:
        return True

    def submit(self, page: Any, timeout_ms: float) -> bool:
        if page is None:
            return False
        try:
            submit_btn = page.locator(
                "button[type='submit'], input[type='submit'], " "button:has-text('Submit'), button:has-text('Apply')"
            )
            if submit_btn and submit_btn.is_visible():
                submit_btn.click(timeout=timeout_ms)
                return True
            return False
        except Exception:
            return False

    def confirm(self, page: Any, timeout_ms: float) -> ConfirmationResult:
        return self._confirmer.confirm(page, timeout_ms)

    @property
    def name(self) -> str:
        return self._name
