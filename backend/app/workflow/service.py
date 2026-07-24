from __future__ import annotations

from typing import Any

from app.workflow.cache import WorkflowCache
from app.workflow.config import WorkflowConfig
from app.workflow.history import WorkflowHistory
from app.workflow.schemas import HistoryEntry, WorkflowState, WorkflowStatus
from app.workflow.state_machine import StateMachine
from app.workflow.transitions import TransitionManager


class WorkflowService:
    def __init__(
        self,
        config: WorkflowConfig | None = None,
    ) -> None:
        self._config = config or WorkflowConfig()
        self._state_machine = StateMachine(self._config)
        self._history = WorkflowHistory()
        self._transitions = TransitionManager(self._state_machine, self._history, self._config)
        self._cache = WorkflowCache(self._config)

    def create_workflow(
        self,
        workflow_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> WorkflowStatus:
        status = WorkflowStatus(
            workflow_id=workflow_id,
            current_state=WorkflowState.DISCOVERED,
            metadata=metadata or {},
        )
        self._cache.set(workflow_id, status)
        return status

    def get_status(self, workflow_id: str) -> WorkflowStatus | None:
        return self._cache.get(workflow_id)

    def transition(
        self,
        workflow_id: str,
        target_state: WorkflowState,
        actor: str = "system",
        reason: str | None = None,
    ) -> WorkflowStatus:
        status = self._cache.get(workflow_id)
        if status is None:
            status = self.create_workflow(workflow_id)

        result = self._transitions.apply(status, target_state, actor, reason)
        self._cache.set(workflow_id, result)
        return result

    def rollback(
        self,
        workflow_id: str,
        actor: str = "system",
        reason: str | None = None,
    ) -> WorkflowStatus:
        status = self._cache.get(workflow_id)
        if status is None:
            status = self.create_workflow(workflow_id)
            return status

        result = self._transitions.rollback(status, actor, reason)
        self._cache.set(workflow_id, result)
        return result

    def get_history(self, workflow_id: str) -> list[HistoryEntry]:
        status = self._cache.get(workflow_id)
        if status is None:
            return []
        return self._history.get_history(workflow_id)

    def can_transition(
        self,
        workflow_id: str,
        target_state: WorkflowState,
    ) -> bool:
        status = self._cache.get(workflow_id)
        if status is None:
            return target_state == WorkflowState.MATCHED
        return self._state_machine.can_transition(status, target_state)

    def is_terminal(self, workflow_id: str) -> bool:
        status = self._cache.get(workflow_id)
        if status is None:
            return False
        return self._state_machine.is_terminal(status.current_state)

    def lock_workflow(self, workflow_id: str) -> WorkflowStatus:
        status = self._cache.get(workflow_id)
        if status is None:
            status = self.create_workflow(workflow_id)
        result = self._transitions.lock(status)
        self._cache.set(workflow_id, result)
        return result

    def unlock_workflow(self, workflow_id: str) -> WorkflowStatus:
        status = self._cache.get(workflow_id)
        if status is None:
            status = self.create_workflow(workflow_id)
        result = self._transitions.unlock(status)
        self._cache.set(workflow_id, result)
        return result

    def invalidate_cache(self, workflow_id: str) -> None:
        self._cache.invalidate(workflow_id)

    def clear_cache(self) -> None:
        self._cache.clear()

    @property
    def state_machine(self) -> StateMachine:
        return self._state_machine
