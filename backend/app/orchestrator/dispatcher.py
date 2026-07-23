from __future__ import annotations

import structlog

from app.orchestrator.exceptions import DispatchError
from app.orchestrator.interfaces import OrchestrationDispatcher
from app.orchestrator.schemas import ExecutionMode, OrchestrationContext, OrchestratorState

logger = structlog.get_logger(__name__)


class ExecutionDispatcher(OrchestrationDispatcher):
    def __init__(self) -> None:
        self._logger = logger.bind(service="orchestrator_dispatcher")

    def dispatch(self, context: OrchestrationContext) -> OrchestrationContext:
        mode = context.execution_mode
        self._logger.info("Dispatching execution", mode=mode.value, id=context.orchestration_id)

        if mode == ExecutionMode.SINGLE:
            return context
        if mode == ExecutionMode.BATCH:
            context.metadata["batch_mode"] = True
            return context
        if mode == ExecutionMode.MANUAL:
            context.state = OrchestratorState.PAUSED
            context.warnings.append("Manual execution — pipeline paused until resumed")
            return context
        if mode == ExecutionMode.DRY_RUN:
            context.warnings.append("Dry run — no submissions will be performed")
            return context
        if mode == ExecutionMode.SCHEDULED:
            context.metadata["scheduled"] = True
            return context
        raise DispatchError(f"Unsupported execution mode: {mode}")
