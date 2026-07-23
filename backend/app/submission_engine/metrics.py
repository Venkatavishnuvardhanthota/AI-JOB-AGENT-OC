from __future__ import annotations

import structlog

from app.submission_engine.interfaces import MetricsTracker
from app.submission_engine.schemas import ExecutionMetrics, StepExecution, SubmissionStepResult, SubmissionStepType

logger = structlog.get_logger(__name__)


class MetricsTrackerEngine(MetricsTracker):
    def __init__(self) -> None:
        self._metrics = ExecutionMetrics()
        self._logger = logger.bind(service="metrics_tracker")

    def record_step(self, step: StepExecution) -> None:
        self._metrics.total_fields += 1

        if step.step_type == SubmissionStepType.UPLOAD:
            self._metrics.upload_count += 1
        elif step.step_type == SubmissionStepType.SKIP:
            self._metrics.skip_count += 1
        elif step.step_type == SubmissionStepType.REQUEST_MANUAL:
            self._metrics.manual_count += 1
        elif (
            step.step_type in (SubmissionStepType.FILL, SubmissionStepType.SELECT, SubmissionStepType.CHECK)
            and step.result == SubmissionStepResult.SUCCESS
        ):
            self._metrics.filled_fields += 1

        if step.result == SubmissionStepResult.SUCCESS:
            self._metrics.success_count += 1
        elif step.result == SubmissionStepResult.FAILED:
            self._metrics.failure_count += 1

        if step.duration_ms is not None:
            if self._metrics.field_execution_duration_ms is None:
                self._metrics.field_execution_duration_ms = 0.0
            self._metrics.field_execution_duration_ms += step.duration_ms

    def get_metrics(self) -> ExecutionMetrics:
        return self._metrics.model_copy()

    def set_upload_duration(self, duration_ms: float) -> None:
        self._metrics.upload_duration_ms = duration_ms

    def set_submit_duration(self, duration_ms: float) -> None:
        self._metrics.submit_duration_ms = duration_ms

    def set_confirmation_duration(self, duration_ms: float) -> None:
        self._metrics.confirmation_duration_ms = duration_ms

    def set_total_duration(self, duration_ms: float) -> None:
        self._metrics.total_duration_ms = duration_ms

    def increment_retry(self) -> None:
        self._metrics.retry_count += 1

    def increment_screenshots(self, count: int = 1) -> None:
        self._metrics.screenshots_taken += count

    def reset(self) -> None:
        self._metrics = ExecutionMetrics()
