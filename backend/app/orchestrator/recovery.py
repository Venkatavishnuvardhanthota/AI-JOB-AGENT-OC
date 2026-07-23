from __future__ import annotations

import time

import structlog

from app.orchestrator.checkpoint import CheckpointManager
from app.orchestrator.config import OrchestratorConfig
from app.orchestrator.exceptions import RecoveryFailedError
from app.orchestrator.schemas import (
    OrchestrationContext,
    PipelineStage,
    RecoveryStrategy,
    RetryHistoryEntry,
    StageStatus,
)

logger = structlog.get_logger(__name__)


class RecoveryHandler:
    def __init__(
        self,
        config: OrchestratorConfig,
        checkpoint_manager: CheckpointManager,
    ) -> None:
        self._config = config
        self._checkpoint_manager = checkpoint_manager
        self._logger = logger.bind(service="orchestrator_recovery")

    def determine_strategy(
        self,
        context: OrchestrationContext,
        stage: PipelineStage,
        error: str,
        attempt: int,
    ) -> RecoveryStrategy:
        stage_result = context.get_stage(stage)

        if attempt >= self._config.max_retries_per_stage:
            if stage_result.checkpoint_id:
                return RecoveryStrategy.RESTART_STAGE
            if context.workflow_id:
                return RecoveryStrategy.ROLLBACK_WORKFLOW
            return RecoveryStrategy.MANUAL_INTERVENTION

        if self._is_retryable(error):
            return RecoveryStrategy.RETRY_STAGE

        if stage_result.checkpoint_id:
            return RecoveryStrategy.RESTART_STAGE

        return RecoveryStrategy.MANUAL_INTERVENTION

    def execute_strategy(
        self,
        context: OrchestrationContext,
        stage: PipelineStage,
        strategy: RecoveryStrategy,
        error: str,
        attempt: int,
    ) -> OrchestrationContext:
        self._logger.info("Executing recovery strategy", stage=stage.value, strategy=strategy.value, attempt=attempt)
        context.get_stage(stage).retry_count += 1

        history = RetryHistoryEntry(stage=stage, attempt=attempt, error=error, strategy=strategy)
        if not hasattr(context, "_retry_history"):
            context._retry_history = []
        context._retry_history.append(history)

        if strategy == RecoveryStrategy.RETRY_STAGE:
            delay = self._config.retry_delay_seconds * (self._config.backoff_multiplier ** (attempt - 1))
            self._logger.info("Retrying stage", stage=stage.value, delay=delay, attempt=attempt)
            time.sleep(delay)
            stage_result = context.get_stage(stage)
            stage_result.status = StageStatus.PENDING
            stage_result.error = None
            return context

        if strategy == RecoveryStrategy.RESTART_STAGE:
            checkpoint = self._checkpoint_manager.load_checkpoint(
                context.get_stage(stage).checkpoint_id
            ) if context.get_stage(stage).checkpoint_id else None
            if checkpoint:
                restored = self._checkpoint_manager.restore_context(checkpoint)
                restored.state = context.state
                restored.current_stage = stage
                restored.get_stage(stage).status = StageStatus.PENDING
                restored.get_stage(stage).error = None
                return restored
            return context

        if strategy == RecoveryStrategy.ROLLBACK_WORKFLOW:
            from app.workflow.dependencies import get_workflow_service
            if context.workflow_id:
                try:
                    wf = get_workflow_service()
                    wf.rollback(context.workflow_id, actor="orchestrator", reason=f"Recovery rollback: {error}")
                except Exception as e:
                    self._logger.error("Workflow rollback failed", error=str(e))
            return context

        if strategy == RecoveryStrategy.MANUAL_INTERVENTION:
            context.warnings.append(f"Manual intervention required at stage {stage.value}: {error}")
            return context

        if strategy == RecoveryStrategy.ABORT:
            raise RecoveryFailedError(f"Aborting after {attempt} attempts at stage {stage.value}: {error}")

        return context

    def _is_retryable(self, error: str) -> bool:
        non_retryable = [
            "invalid", "unauthorized", "forbidden", "not found",
            "validation error", "bad request",
        ]
        error_lower = error.lower()
        return not any(nr in error_lower for nr in non_retryable)
