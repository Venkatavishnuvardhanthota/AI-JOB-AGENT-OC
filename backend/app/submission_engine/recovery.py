from __future__ import annotations

import time
from typing import Any

import structlog

from app.submission_engine.config import SubmissionEngineConfig
from app.submission_engine.exceptions import SubmissionRecoveryError
from app.submission_engine.interfaces import SubmissionRecovery
from app.submission_engine.schemas import RetryAttempt

logger = structlog.get_logger(__name__)

NON_RETRYABLE_ERRORS = [
    "validation failed",
    "invalid selector",
    "element not found",
    "field is not visible",
    "not allowed",
    "rejected",
    "unauthorized",
    "forbidden",
]


class SubmissionRecoveryHandler(SubmissionRecovery):
    def __init__(self, config: SubmissionEngineConfig | None = None) -> None:
        self._config = config or SubmissionEngineConfig()
        self._attempts: list[RetryAttempt] = []
        self._logger = logger.bind(service="submission_recovery")

    def can_retry(self, error: str, attempt: int) -> bool:
        if attempt >= self._config.max_retry_attempts:
            return False
        error_lower = error.lower()
        return all(non_retryable not in error_lower for non_retryable in NON_RETRYABLE_ERRORS)

    def recover(self, page: Any, error: str, attempt: int) -> bool:
        if not self.can_retry(error, attempt):
            raise SubmissionRecoveryError(f"Recovery not possible for error: {error}")

        delay = self._compute_delay(attempt)
        self._logger.info("Attempting recovery", attempt=attempt, delay=delay)
        time.sleep(delay)

        try:
            if page is not None:
                current_url = page.url
                if current_url and "error" not in current_url.lower():
                    return True
        except Exception:
            pass

        return True

    def record_attempt(self, error: str, duration_ms: float | None = None) -> RetryAttempt:
        attempt_num = len(self._attempts) + 1
        attempt = RetryAttempt(
            attempt_number=attempt_num,
            error=error,
            duration_ms=duration_ms,
        )
        self._attempts.append(attempt)
        return attempt

    def get_attempts(self) -> list[RetryAttempt]:
        return list(self._attempts)

    def reset(self) -> None:
        self._attempts.clear()

    def _compute_delay(self, attempt: int) -> float:
        delay = self._config.retry_delay_seconds * (self._config.backoff_multiplier ** (attempt - 1))
        return min(delay, self._config.max_retry_delay_seconds)
