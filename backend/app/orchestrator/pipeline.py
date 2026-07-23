from __future__ import annotations

import structlog

from app.orchestrator.checkpoint import CheckpointManager
from app.orchestrator.config import OrchestratorConfig
from app.orchestrator.exceptions import (
    ManualInterventionError,
    NonRecoverableError,
    RecoverableError,
    StageExecutionError,
)
from app.orchestrator.interfaces import PipelineStageExecutor
from app.orchestrator.metrics import OrchestratorMetricsCollector
from app.orchestrator.recovery import RecoveryHandler
from app.orchestrator.schemas import (
    ExecutionMode,
    OrchestrationContext,
    OrchestratorState,
    PipelineStage,
    RecoveryStrategy,
    StageStatus,
)
from app.orchestrator.state import OrchestrationStateManager

logger = structlog.get_logger(__name__)


class PipelineEngine:
    def __init__(
        self,
        config: OrchestratorConfig,
        checkpoint_manager: CheckpointManager,
        recovery_handler: RecoveryHandler,
        metrics_collector: OrchestratorMetricsCollector,
        state_manager: OrchestrationStateManager,
        stage_executors: list[PipelineStageExecutor],
    ) -> None:
        self._config = config
        self._checkpoint_manager = checkpoint_manager
        self._recovery = recovery_handler
        self._metrics = metrics_collector
        self._state = state_manager
        self._executors: dict[PipelineStage, PipelineStageExecutor] = {
            e.stage(): e for e in stage_executors
        }
        self._logger = logger.bind(service="orchestrator_pipeline")

    def run(self, context: OrchestrationContext) -> OrchestrationContext:
        self._state.set_running(context)
        context.started_at = __import__("datetime").datetime.utcnow()

        if context.execution_mode == ExecutionMode.DRY_RUN:
            context.warnings.append("Dry run pipeline")
            return self._state.set_completed(context)

        stages = [
            PipelineStage.PROFILE_INTELLIGENCE,
            PipelineStage.JOB_DISCOVERY,
            PipelineStage.JOB_MATCHING,
            PipelineStage.APPLICATION_INTELLIGENCE,
            PipelineStage.RESUME_OPTIMIZATION,
            PipelineStage.COVER_LETTER,
            PipelineStage.APPLICATION_PACKAGE,
            PipelineStage.REVIEW,
            PipelineStage.WORKFLOW,
            PipelineStage.ATS_DETECTION,
            PipelineStage.FORM_INTELLIGENCE,
            PipelineStage.UPLOAD,
            PipelineStage.SUBMISSION,
            PipelineStage.TRACKING,
        ]

        for stage in stages:
            if self._state.is_completed(context) or context.state == OrchestratorState.PAUSED:
                break

            context = self._state.set_current_stage(context, stage)
            executor = self._executors.get(stage)
            if executor is None:
                context = self._skip_stage(context, stage, "No executor registered")
                continue

            context = self._execute_with_recovery(context, stage, executor)

        return self._state.set_completed(context)

    def _execute_with_recovery(
        self,
        context: OrchestrationContext,
        stage: PipelineStage,
        executor: PipelineStageExecutor,
    ) -> OrchestrationContext:
        if executor.should_skip(context):
            return self._skip_stage(context, stage, "Skipped by executor")

        max_attempts = 1 + self._config.max_retries_per_stage
        for attempt in range(1, max_attempts + 1):
            try:
                result = context.get_stage(stage)
                result.status = StageStatus.RUNNING
                result.started_at = __import__("datetime").datetime.utcnow()
                self._metrics.record_stage_start(stage, context)

                context = executor.execute(context)

                self._metrics.record_stage_end(stage, context)
                result.status = StageStatus.COMPLETED
                result.completed_at = __import__("datetime").datetime.utcnow()

                if self._config.checkpoint_enabled:
                    try:
                        ck = self._checkpoint_manager.create_checkpoint(context, stage)
                        result.checkpoint_id = ck.checkpoint_id
                    except Exception as e:
                        self._logger.warning("Checkpoint creation failed", stage=stage.value, error=str(e))

                return context

            except (StageExecutionError, RecoverableError) as e:
                self._logger.warning("Recoverable stage error", stage=stage.value, attempt=attempt, error=str(e))
                strategy = self._recovery.determine_strategy(context, stage, str(e), attempt)
                context = self._recovery.execute_strategy(context, stage, strategy, str(e), attempt)
                if strategy == RecoveryStrategy.MANUAL_INTERVENTION:
                    context.state = OrchestratorState.PAUSED
                    context.warnings.append(f"Paused for manual intervention at {stage.value}: {e}")
                    return context
                if strategy == RecoveryStrategy.ABORT:
                    return self._state.set_failed(context, str(e))

            except (NonRecoverableError, ManualInterventionError) as e:
                self._logger.error("Non-recoverable stage error", stage=stage.value, error=str(e))
                return self._state.set_failed(context, str(e))

        return self._state.set_failed(context, f"Max retries exceeded for stage {stage.value}")

    def _skip_stage(self, context: OrchestrationContext, stage: PipelineStage, reason: str) -> OrchestrationContext:
        context.mark_stage_skipped(stage, reason)
        return context
