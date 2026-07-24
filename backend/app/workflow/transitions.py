from __future__ import annotations

from app.workflow.config import WorkflowConfig
from app.workflow.exceptions import WorkflowLockedError
from app.workflow.history import WorkflowHistory
from app.workflow.schemas import (
    HistoryEntry,
    TransitionType,
    WorkflowState,
    WorkflowStatus,
)
from app.workflow.state_machine import StateMachine
from app.workflow.validator import WorkflowValidator


class TransitionManager:
    def __init__(
        self,
        state_machine: StateMachine,
        history: WorkflowHistory,
        config: WorkflowConfig | None = None,
    ) -> None:
        self._state_machine = state_machine
        self._history = history
        self._config = config or WorkflowConfig()
        self._validator = WorkflowValidator(
            strict=self._config.strict_validation,
            max_retries=self._config.max_retries,
        )

    def apply(
        self,
        status: WorkflowStatus,
        target_state: WorkflowState,
        actor: str = "system",
        reason: str | None = None,
    ) -> WorkflowStatus:
        if status.locked:
            raise WorkflowLockedError(message="Workflow is locked and cannot process transitions.")

        from_state = status.current_state
        is_retry = from_state == target_state

        if is_retry:
            self._validator.validate_retry(status)
            status.retry_count += 1
        else:
            self._state_machine.transition(status, target_state)

        if self._config.track_history:
            entry = HistoryEntry(
                from_state=from_state,
                to_state=status.current_state,
                actor=actor,
                transition_type=TransitionType.RETRY if is_retry else TransitionType.TRANSITION,
                reason=reason,
                success=True,
            )
            self._history.add(status.workflow_id, entry)

        return status

    def rollback(
        self,
        status: WorkflowStatus,
        actor: str = "system",
        reason: str | None = None,
    ) -> WorkflowStatus:
        if status.locked:
            raise WorkflowLockedError(message="Workflow is locked and cannot process rollback.")

        from_state = status.current_state
        self._state_machine.rollback(status)

        if self._config.track_history:
            entry = HistoryEntry(
                from_state=from_state,
                to_state=status.current_state,
                actor=actor,
                transition_type=TransitionType.ROLLBACK,
                reason=reason,
                success=True,
            )
            self._history.add(status.workflow_id, entry)

        return status

    def lock(self, status: WorkflowStatus) -> WorkflowStatus:
        status.locked = True
        return status

    def unlock(self, status: WorkflowStatus) -> WorkflowStatus:
        status.locked = False
        return status
