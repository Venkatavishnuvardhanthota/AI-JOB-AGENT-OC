from __future__ import annotations

from datetime import datetime
from typing import Any

from app.submission.cache import SubmissionCache
from app.submission.config import SubmissionConfig
from app.submission.dispatcher import Dispatcher
from app.submission.exceptions import SubmissionNotFoundError
from app.submission.queue import SubmissionQueue
from app.submission.retry import RetryHandler
from app.submission.scheduler import Scheduler
from app.submission.schemas import (
    QueueItem,
    QueueStatistics,
    StrategyType,
    SubmissionPriority,
    SubmissionRecord,
    SubmissionState,
)
from app.submission.validator import SubmissionValidator


class SubmissionService:
    def __init__(
        self,
        config: SubmissionConfig | None = None,
    ) -> None:
        self._config = config or SubmissionConfig()
        self._validator = SubmissionValidator(strict=self._config.strict_validation)
        self._queue = SubmissionQueue()
        self._scheduler = Scheduler()
        self._retry = RetryHandler(self._config)
        self._dispatcher = Dispatcher(self._retry)
        self._cache = SubmissionCache(self._config)

    def create_submission(
        self,
        package_id: str,
        workflow_id: str | None = None,
        tracking_id: str | None = None,
        review_id: str | None = None,
        priority: SubmissionPriority = SubmissionPriority.MEDIUM,
        strategy: StrategyType = StrategyType.MANUAL,
        dry_run: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> SubmissionRecord:
        existing = self._cache.get(package_id)
        self._validator.validate_create(package_id, existing)

        record = SubmissionRecord(
            package_id=package_id,
            workflow_id=workflow_id,
            tracking_id=tracking_id,
            review_id=review_id,
            priority=priority,
            strategy=strategy,
            dry_run=dry_run,
            metadata=metadata or {},
            retry=self._retry.make_retry_record(),
        )
        self._cache.set(package_id, record)
        return record

    def validate(
        self,
        package_id: str,
        review_status: str | None = None,
        workflow_status: str | None = None,
        is_package_complete: bool = False,
        has_job_posting: bool = False,
        has_resume: bool = False,
        has_cover_letter: bool = False,
    ) -> SubmissionRecord:
        record = self._get_submission(package_id)

        from app.review.schemas import ReviewState as ReviewStateEnum
        from app.workflow.schemas import WorkflowState as WorkflowStateEnum

        review = type("Review", (), {"state": ReviewStateEnum(review_status)})() if review_status else None
        wf_state_obj = WorkflowStateEnum(workflow_status) if workflow_status else None

        self._validator.validate_submission_readiness(
            review, wf_state_obj, is_package_complete,
            has_job_posting, has_resume, has_cover_letter,
        )

        record.state = SubmissionState.VALIDATED
        record.updated_at = datetime.utcnow()
        self._cache.set(package_id, record)
        return record

    def queue(
        self,
        package_id: str,
        scheduled_at: datetime | None = None,
    ) -> SubmissionRecord:
        record = self._get_submission(package_id)
        self._validator.validate_state_transition(
            record, SubmissionState.QUEUED
        )
        self._queue.enqueue(record, scheduled_at)
        self._cache.set(package_id, record)
        return record

    def dispatch(
        self,
        package_id: str,
        strategy_type: StrategyType | None = None,
    ) -> SubmissionRecord:
        record = self._get_submission(package_id)
        self._validator.validate_state_transition(
            record, SubmissionState.DISPATCHED
        )
        result = self._dispatcher.dispatch(record, strategy_type)
        self._cache.set(package_id, result)
        return result

    def cancel(
        self,
        package_id: str,
        reason: str | None = None,
    ) -> SubmissionRecord:
        record = self._get_submission(package_id)
        self._validator.validate_cancel(record)
        record.state = SubmissionState.CANCELLED
        record.updated_at = datetime.utcnow()
        if reason:
            record.errors.append(reason)
        self._queue.remove(record.id)
        self._cache.set(package_id, record)
        return record

    def retry(
        self,
        package_id: str,
    ) -> SubmissionRecord:
        record = self._get_submission(package_id)
        self._validator.validate_retry(record)
        self._retry.reset(record)
        record.state = SubmissionState.QUEUED
        record.updated_at = datetime.utcnow()
        self._queue.enqueue(record)
        self._cache.set(package_id, record)
        return record

    def get_status(self, package_id: str) -> SubmissionRecord | None:
        return self._cache.get(package_id)

    def get_queue(
        self,
        priority: SubmissionPriority | None = None,
    ) -> list[QueueItem]:
        return self._queue.get_queue(priority)

    def get_queue_statistics(self) -> QueueStatistics:
        return self._queue.get_statistics()

    def update_priority(
        self,
        package_id: str,
        priority: SubmissionPriority,
    ) -> SubmissionRecord:
        record = self._get_submission(package_id)
        record.priority = priority
        self._queue.update_priority(record.id, priority)
        self._cache.set(package_id, record)
        return record

    def invalidate_cache(self, package_id: str) -> None:
        self._cache.invalidate(package_id)

    def clear_cache(self) -> None:
        self._cache.clear()

    def _get_submission(self, package_id: str) -> SubmissionRecord:
        record = self._cache.get(package_id)
        if record is None:
            raise SubmissionNotFoundError(
                message=f"No submission found for package '{package_id}'."
            )
        return record
