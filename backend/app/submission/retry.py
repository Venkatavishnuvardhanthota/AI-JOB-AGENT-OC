from __future__ import annotations

from datetime import datetime, timedelta

from app.submission.config import SubmissionConfig
from app.submission.schemas import RetryRecord, SubmissionRecord, SubmissionState


class RetryHandler:
    def __init__(self, config: SubmissionConfig | None = None) -> None:
        self._config = config or SubmissionConfig()

    def can_retry(self, record: SubmissionRecord) -> bool:
        if record.retry.non_retryable:
            return False
        return record.retry.attempt < record.retry.max_retries

    def get_retry_delay(self, record: SubmissionRecord) -> float:
        attempt = record.retry.attempt
        base = record.retry.retry_delay_seconds
        multiplier = record.retry.backoff_multiplier
        return base * (multiplier ** attempt)

    def record_attempt(
        self,
        record: SubmissionRecord,
        error: str | None = None,
        non_retryable: bool = False,
    ) -> SubmissionRecord:
        record.retry.attempt += 1
        record.retry.last_attempt_at = datetime.utcnow()

        if error:
            record.retry.errors.append(error)

        if non_retryable:
            record.retry.non_retryable = True
            record.state = SubmissionState.FAILED
            record.failed_at = datetime.utcnow()
            return record

        if record.retry.attempt >= record.retry.max_retries:
            record.state = SubmissionState.FAILED
            record.failed_at = datetime.utcnow()
            return record

        delay = self.get_retry_delay(record)
        record.retry.next_retry_at = datetime.utcnow() + timedelta(seconds=delay)
        record.state = SubmissionState.QUEUED
        return record

    def mark_non_retryable(
        self,
        record: SubmissionRecord,
        error: str,
    ) -> SubmissionRecord:
        record.retry.non_retryable = True
        record.retry.errors.append(error)
        record.state = SubmissionState.FAILED
        record.failed_at = datetime.utcnow()
        return record

    def make_retry_record(self) -> RetryRecord:
        return RetryRecord(
            max_retries=self._config.default_max_retries,
            retry_delay_seconds=self._config.default_retry_delay_seconds,
            backoff_multiplier=self._config.retry_backoff_multiplier,
        )

    def reset(self, record: SubmissionRecord) -> SubmissionRecord:
        record.retry.attempt = 0
        record.retry.last_attempt_at = None
        record.retry.next_retry_at = None
        record.retry.errors = []
        record.retry.non_retryable = False
        return record
