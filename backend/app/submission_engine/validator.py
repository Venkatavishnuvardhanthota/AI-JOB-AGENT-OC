from __future__ import annotations

from typing import Any

import structlog

from app.submission_engine.config import SubmissionEngineConfig
from app.submission_engine.interfaces import SubmissionValidator
from app.submission_engine.schemas import SubmissionState, SubmissionStatus

logger = structlog.get_logger(__name__)


class SubmissionValidatorEngine(SubmissionValidator):
    def __init__(self, config: SubmissionEngineConfig | None = None) -> None:
        self._config = config or SubmissionEngineConfig()
        self._logger = logger.bind(service="submission_validator")

    def validate(self, page: Any, execution_plan: Any, upload_plan: Any | None = None) -> list[str]:
        issues: list[str] = []

        issues.extend(self._validate_page(page))
        issues.extend(self._validate_execution_plan(execution_plan))
        issues.extend(self._validate_upload_plan(upload_plan))

        return issues

    def validate_pre_submit(
        self, status: SubmissionStatus, execution_plan: Any,
        upload_results: list[Any] | None = None
    ) -> list[str]:
        issues: list[str] = []

        if status.state not in (SubmissionState.AWAITING_CONFIRMATION, SubmissionState.EXECUTING_UPLOADS):
            issues.append(
                f"Submission is in '{status.state.value}' state, "
                "expected 'awaiting_confirmation' or 'executing_uploads'"
            )

        issues.extend(self._check_required_fields(execution_plan))
        issues.extend(self._check_required_uploads(upload_results))

        if upload_results:
            issues.extend(self._check_upload_results(upload_results))

        return issues

    def _validate_page(self, page: Any) -> list[str]:
        issues: list[str] = []
        if page is None:
            issues.append("Browser page is not available")
        return issues

    def _validate_execution_plan(self, execution_plan: Any) -> list[str]:
        issues: list[str] = []
        if execution_plan is None:
            issues.append("Execution plan is not provided")
            return issues

        steps = getattr(execution_plan, "steps", [])
        if not steps:
            issues.append("Execution plan has no steps")

        return issues

    def _validate_upload_plan(self, upload_plan: Any) -> list[str]:
        issues: list[str] = []
        if upload_plan is None:
            return issues

        tasks = getattr(upload_plan, "tasks", [])
        if not tasks:
            issues.append("Upload plan has no tasks")

        return issues

    def _check_required_fields(self, execution_plan: Any) -> list[str]:
        issues: list[str] = []
        if execution_plan is None:
            return issues

        steps = getattr(execution_plan, "steps", [])
        for step in steps:
            step_type = getattr(step, "step_type", None)
            step_type_str = str(step_type.value) if hasattr(step_type, "value") else str(step_type)
            requires_manual = getattr(step, "requires_manual_review", False)

            if step_type_str == "request_manual" and requires_manual and self._config.require_manual_tasks_resolved:
                field_ref = getattr(step, "field_ref", "unknown")
                issues.append(f"Manual task '{field_ref}' requires resolution before submission")

        return issues

    def _check_required_uploads(self, upload_results: list[Any] | None) -> list[str]:
        issues: list[str] = []
        if not upload_results:
            if self._config.require_uploads_complete:
                issues.append("No upload results available")
            return issues

        for result in upload_results:
            result_value = getattr(result, "result", None)
            if result_value is not None:
                result_str = str(result_value.value) if hasattr(result_value, "value") else str(result_value)
                if result_str in ("failed", "timeout", "rejected", "verification_failed"):
                    field_ref = getattr(result, "field_ref", "unknown")
                    issues.append(f"Required upload '{field_ref}' failed: {result_str}")

        return issues

    def _check_upload_results(self, upload_results: list[Any]) -> list[str]:
        issues: list[str] = []
        for result in upload_results:
            result_value = getattr(result, "result", None)
            if result_value is not None:
                result_str = str(result_value.value) if hasattr(result_value, "value") else str(result_value)
                if result_str in ("failed", "timeout", "rejected"):
                    field_ref = getattr(result, "field_ref", "unknown")
                    issues.append(f"Upload '{field_ref}' has non-retryable error: {result_str}")
        return issues

    def validate_workflow(self, workflow_service: Any, workflow_id: str) -> list[str]:
        issues: list[str] = []
        if not self._config.require_workflow_ready:
            return issues

        if workflow_service is None:
            issues.append("Workflow service is not available")
            return issues

        try:
            status = workflow_service.get_status(workflow_id)
            if status is None:
                issues.append(f"Workflow '{workflow_id}' not found")
                return issues

            from app.workflow.schemas import WorkflowState
            current = getattr(status, "current_state", None)
            allowed = [WorkflowState.APPROVED, WorkflowState.QUEUED]
            if current not in allowed:
                issues.append(
                    f"Workflow state '{current.value if hasattr(current, 'value') else current}' "
                    "not ready for submission"
                )
        except Exception as e:
            issues.append(f"Failed to check workflow: {e}")

        return issues

    def validate_review(self, review_service: Any, package_id: str) -> list[str]:
        issues: list[str] = []
        if not self._config.require_review_approval:
            return issues

        if review_service is None:
            issues.append("Review service is not available")
            return issues

        try:
            record = review_service.get_review(package_id)
            if record is None:
                issues.append(f"No review found for package '{package_id}'")
                return issues

            from app.review.schemas import ReviewState
            state = getattr(record, "state", None)
            if state != ReviewState.APPROVED:
                issues.append(
                    f"Review state is '{state.value if hasattr(state, 'value') else state}', "
                    "expected 'approved'"
                )
        except Exception as e:
            issues.append(f"Failed to check review: {e}")

        return issues
