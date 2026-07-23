from __future__ import annotations

from app.workflow.config import WorkflowConfig
from app.workflow.schemas import WorkflowState, WorkflowStatus
from app.workflow.validator import WorkflowValidator


class StateMachine:
    def __init__(
        self,
        config: WorkflowConfig | None = None,
    ) -> None:
        self._config = config or WorkflowConfig()
        self._validator = WorkflowValidator(
            strict=self._config.strict_validation,
            max_retries=self._config.max_retries,
        )

    def transition(
        self,
        status: WorkflowStatus,
        target_state: WorkflowState,
    ) -> WorkflowStatus:
        self._validator.validate_transition(status, target_state)

        if status.current_state == target_state:
            status.retry_count += 1
            return status

        status.previous_state = status.current_state
        status.current_state = target_state
        status.retry_count = 0
        return status

    def rollback(
        self,
        status: WorkflowStatus,
    ) -> WorkflowStatus:
        self._validator.validate_rollback(status)

        if status.previous_state is None:
            return status

        status.current_state = status.previous_state
        status.previous_state = None
        status.retry_count = 0
        return status

    def can_transition(
        self,
        status: WorkflowStatus,
        target_state: WorkflowState,
    ) -> bool:
        allowed = self._validator._get_allowed_transitions(status.current_state)  # noqa: SLF001
        return target_state in allowed

    def is_terminal(self, state: WorkflowState) -> bool:
        return state == WorkflowState.REJECTED

    def get_allowed_transitions(
        self,
        state: WorkflowState,
    ) -> list[WorkflowState]:
        return self._validator._get_allowed_transitions(state)  # noqa: SLF001
