from __future__ import annotations

from app.workflow.exceptions import InvalidTransitionError, MaxRetriesExceededError
from app.workflow.schemas import WorkflowState, WorkflowStatus


class WorkflowValidator:
    def __init__(self, strict: bool = True, max_retries: int = 3) -> None:
        self._strict = strict
        self._max_retries = max_retries

    def validate_transition(
        self,
        status: WorkflowStatus,
        target_state: WorkflowState,
    ) -> None:
        current = status.current_state
        allowed = self.get_allowed_transitions(current)

        if current == target_state:
            return

        if target_state not in allowed:
            raise InvalidTransitionError(
                message=f"Cannot transition from {current.value} to {target_state.value}. "
                f"Allowed transitions from {current.value}: {[s.value for s in allowed]}"
            )

    def validate_retry(
        self,
        status: WorkflowStatus,
    ) -> None:
        if status.retry_count >= self._max_retries:
            raise MaxRetriesExceededError(
                message=f"Maximum retry attempts ({self._max_retries}) exceeded."
            )

    def validate_rollback(
        self,
        status: WorkflowStatus,
    ) -> None:
        if not self._strict:
            return
        if status.previous_state is None:
            raise InvalidTransitionError(
                message="Cannot rollback: no previous state available."
            )

    @staticmethod
    def get_allowed_transitions(state: WorkflowState) -> list[WorkflowState]:
        transitions = {
            WorkflowState.DISCOVERED: [WorkflowState.MATCHED],
            WorkflowState.MATCHED: [WorkflowState.PACKAGE_GENERATED],
            WorkflowState.PACKAGE_GENERATED: [WorkflowState.READY_FOR_REVIEW],
            WorkflowState.READY_FOR_REVIEW: [
                WorkflowState.APPROVED,
                WorkflowState.REJECTED,
            ],
            WorkflowState.APPROVED: [WorkflowState.QUEUED],
            WorkflowState.QUEUED: [WorkflowState.SUBMITTED],
            WorkflowState.SUBMITTED: [WorkflowState.TRACKING],
            WorkflowState.TRACKING: [WorkflowState.INTERVIEW, WorkflowState.REJECTED],
            WorkflowState.INTERVIEW: [WorkflowState.OFFER, WorkflowState.REJECTED],
            WorkflowState.OFFER: [WorkflowState.REJECTED],
            WorkflowState.REJECTED: [],
        }
        return transitions.get(state, [])
