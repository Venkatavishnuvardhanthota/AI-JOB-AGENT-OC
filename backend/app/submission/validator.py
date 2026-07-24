from __future__ import annotations

from app.review.schemas import ReviewRecord, ReviewState
from app.submission.exceptions import (
    DuplicateSubmissionError,
    InvalidSubmissionStateError,
    SubmissionNotFoundError,
    SubmissionNotReadyError,
    SubmissionValidationError,
)
from app.submission.schemas import SubmissionRecord, SubmissionState
from app.workflow.schemas import WorkflowState


class SubmissionValidator:
    def __init__(self, strict: bool = True) -> None:
        self._strict = strict

    def validate_create(
        self,
        package_id: str,
        existing: SubmissionRecord | None,
    ) -> None:
        if existing is not None:
            raise DuplicateSubmissionError(message=f"Submission already exists for package '{package_id}'.")

    def validate_get(self, record: SubmissionRecord | None) -> SubmissionRecord:
        if record is None:
            raise SubmissionNotFoundError(message="Submission record not found.")
        return record

    def validate_submission_readiness(
        self,
        review: ReviewRecord | None,
        workflow_state: WorkflowState | None,
        is_package_complete: bool,
        has_job_posting: bool,
        has_resume: bool,
        has_cover_letter: bool,
    ) -> None:
        failures: list[str] = []

        if review is None or review.state not in (
            ReviewState.APPROVED,
            ReviewState.AUTO_APPROVED,
        ):
            failures.append("Application has not been approved")

        if workflow_state != WorkflowState.QUEUED:
            failures.append(
                f"Workflow is not in QUEUED state (current: {workflow_state.value if workflow_state else 'None'})"
            )

        if not is_package_complete:
            failures.append("Application package is not complete")

        if not has_job_posting:
            failures.append("Job posting is missing")

        if not has_resume:
            failures.append("Optimized resume is missing")

        if not has_cover_letter:
            failures.append("Cover letter is missing")

        if failures:
            raise SubmissionNotReadyError(message="Application is not ready for submission: " + "; ".join(failures))

    def validate_state_transition(
        self,
        record: SubmissionRecord,
        target_state: SubmissionState,
    ) -> None:
        allowed = self._get_allowed_transitions(record.state)
        if target_state not in allowed:
            raise InvalidSubmissionStateError(
                message=f"Cannot transition from {record.state.value} "
                f"to {target_state.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )

    def validate_cancel(
        self,
        record: SubmissionRecord,
    ) -> None:
        cancellable = [
            SubmissionState.PENDING,
            SubmissionState.VALIDATED,
            SubmissionState.QUEUED,
            SubmissionState.SCHEDULED,
        ]
        if record.state not in cancellable:
            raise InvalidSubmissionStateError(
                message=f"Cannot cancel submission in state '{record.state.value}'. "
                f"Only cancellable: {[s.value for s in cancellable]}"
            )

    def validate_retry(
        self,
        record: SubmissionRecord,
    ) -> None:
        if record.state != SubmissionState.FAILED:
            raise InvalidSubmissionStateError(
                message=f"Cannot retry submission in state '{record.state.value}'. "
                "Only FAILED submissions can be retried."
            )
        if record.retry.non_retryable:
            raise SubmissionValidationError(message="This failure is non-retryable.")

    @staticmethod
    def _get_allowed_transitions(
        state: SubmissionState,
    ) -> list[SubmissionState]:
        transitions: dict[SubmissionState, list[SubmissionState]] = {
            SubmissionState.PENDING: [
                SubmissionState.VALIDATED,
                SubmissionState.CANCELLED,
            ],
            SubmissionState.VALIDATED: [
                SubmissionState.QUEUED,
                SubmissionState.CANCELLED,
            ],
            SubmissionState.QUEUED: [
                SubmissionState.SCHEDULED,
                SubmissionState.DISPATCHED,
                SubmissionState.CANCELLED,
            ],
            SubmissionState.SCHEDULED: [
                SubmissionState.DISPATCHED,
                SubmissionState.CANCELLED,
            ],
            SubmissionState.DISPATCHED: [
                SubmissionState.RUNNING,
                SubmissionState.FAILED,
            ],
            SubmissionState.RUNNING: [
                SubmissionState.COMPLETED,
                SubmissionState.FAILED,
            ],
            SubmissionState.COMPLETED: [],
            SubmissionState.FAILED: [
                SubmissionState.QUEUED,
                SubmissionState.CANCELLED,
            ],
            SubmissionState.CANCELLED: [],
        }
        return transitions.get(state, [])
