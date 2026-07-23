from __future__ import annotations

from typing import Any

import structlog

from app.orchestrator.checkpoint import CheckpointManager
from app.orchestrator.config import OrchestratorConfig
from app.orchestrator.coordinator import (
    ApplicationIntelligenceExecutor,
    ApplicationPackageExecutor,
    ATSDetectionExecutor,
    CoverLetterExecutor,
    FormIntelligenceExecutor,
    JobDiscoveryExecutor,
    JobMatchingExecutor,
    ProfileIntelligenceExecutor,
    ResumeOptimizationExecutor,
    ReviewExecutor,
    SubmissionExecutor,
    TrackingExecutor,
    UploadExecutor,
    WorkflowExecutor,
)
from app.orchestrator.dispatcher import ExecutionDispatcher
from app.orchestrator.exceptions import CheckpointError
from app.orchestrator.metrics import OrchestratorMetricsCollector
from app.orchestrator.pipeline import PipelineEngine
from app.orchestrator.recovery import RecoveryHandler
from app.orchestrator.reporting import OrchestrationReportBuilder
from app.orchestrator.schemas import (
    ExecutionMode,
    OrchestrationContext,
    OrchestrationReport,
    OrchestratorState,
    PipelineStage,
)
from app.orchestrator.state import OrchestrationStateManager
from app.orchestrator.validator import OrchestratorValidator

logger = structlog.get_logger(__name__)


class OrchestratorService:
    def __init__(
        self,
        config: OrchestratorConfig | None = None,
    ) -> None:
        self._config = config or OrchestratorConfig()
        self._validator = OrchestratorValidator(self._config)
        self._state_manager = OrchestrationStateManager()
        self._checkpoint_manager = CheckpointManager(self._config.checkpoint_dir)
        self._metrics_collector = OrchestratorMetricsCollector()
        self._recovery_handler = RecoveryHandler(self._config, self._checkpoint_manager)
        self._dispatcher = ExecutionDispatcher()
        self._report_builder = OrchestrationReportBuilder(self._metrics_collector)
        self._logger = logger.bind(service="orchestrator")

        self._stage_executors = [
            ProfileIntelligenceExecutor(),
            JobDiscoveryExecutor(),
            JobMatchingExecutor(),
            ApplicationIntelligenceExecutor(),
            ResumeOptimizationExecutor(),
            CoverLetterExecutor(),
            ApplicationPackageExecutor(),
            ReviewExecutor(),
            WorkflowExecutor(),
            ATSDetectionExecutor(),
            FormIntelligenceExecutor(),
            UploadExecutor(),
            SubmissionExecutor(),
            TrackingExecutor(),
        ]

        self._pipeline = PipelineEngine(
            config=self._config,
            checkpoint_manager=self._checkpoint_manager,
            recovery_handler=self._recovery_handler,
            metrics_collector=self._metrics_collector,
            state_manager=self._state_manager,
            stage_executors=self._stage_executors,
        )

    def run(
        self,
        job: Any = None,
        profile: Any = None,
        user_id: Any = None,
        execution_mode: str | ExecutionMode = ExecutionMode.SINGLE,
        workflow_id: str | None = None,
        tracking_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> OrchestrationReport:
        mode = self._validator.validate_mode(execution_mode)

        context = OrchestrationContext(
            execution_mode=mode,
            job=job,
            profile=profile,
            user_id=user_id,
            workflow_id=workflow_id,
            tracking_id=tracking_id,
            metadata=metadata or {},
        )

        self._logger.info("Starting orchestration", id=context.orchestration_id, mode=mode.value)
        context = self._dispatcher.dispatch(context)

        if context.state == OrchestratorState.PAUSED:
            return self._report_builder.build(context)

        context = self._pipeline.run(context)
        report = self._report_builder.build(context)
        self._logger.info("Orchestration completed", id=context.orchestration_id, state=context.state.value)
        return report

    def resume(self, checkpoint_id: str) -> OrchestrationReport:
        checkpoint = self._checkpoint_manager.load_checkpoint(checkpoint_id)
        if checkpoint is None:
            raise CheckpointError(f"Checkpoint '{checkpoint_id}' not found")

        context = self._checkpoint_manager.restore_context(checkpoint)
        if not self._state_manager.can_resume(context):
            raise CheckpointError(f"Cannot resume orchestration in state '{context.state.value}'")

        self._logger.info("Resuming orchestration", id=context.orchestration_id, checkpoint=checkpoint_id)
        context = self._pipeline.run(context)
        report = self._report_builder.build(context)
        return report

    def get_status(self, orchestration_id: str) -> OrchestrationReport | None:
        checkpoints = self._checkpoint_manager.list_checkpoints(orchestration_id)
        if not checkpoints:
            return None
        latest = checkpoints[-1]
        context = self._checkpoint_manager.restore_context(latest)
        return self._report_builder.build(context)

    def cancel(self, orchestration_id: str, reason: str = "") -> None:
        self._checkpoint_manager.clear_all(orchestration_id)
        self._logger.info("Orchestration cancelled", id=orchestration_id, reason=reason)

    def list_checkpoints(self, orchestration_id: str) -> list[dict[str, Any]]:
        checkpoints = self._checkpoint_manager.list_checkpoints(orchestration_id)
        return [c.model_dump() for c in checkpoints]

    def get_available_stages(self) -> list[str]:
        return [s.value for s in PipelineStage]

    def validate_mode(self, mode: str) -> None:
        self._validator.validate_mode(mode)

    def clear_checkpoints(self, orchestration_id: str) -> None:
        self._checkpoint_manager.clear_all(orchestration_id)
