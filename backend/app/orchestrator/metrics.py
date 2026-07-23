from __future__ import annotations

from datetime import datetime

from app.orchestrator.interfaces import MetricsCollector
from app.orchestrator.schemas import (
    OrchestrationContext,
    OrchestrationMetrics,
    PipelineStage,
    StageStatus,
)


class OrchestratorMetricsCollector(MetricsCollector):
    def __init__(self) -> None:
        self._stage_start: dict[str, datetime] = {}

    def record_stage_start(self, stage: PipelineStage, context: OrchestrationContext) -> None:
        self._stage_start[stage.value] = datetime.utcnow()

    def record_stage_end(self, stage: PipelineStage, context: OrchestrationContext) -> None:
        start = self._stage_start.pop(stage.value, None)
        if start is not None:
            duration_ms = (datetime.utcnow() - start).total_seconds() * 1000
            result = context.get_stage(stage)
            result.duration_ms = duration_ms

    def get_metrics(self, context: OrchestrationContext) -> OrchestrationMetrics:
        metrics = OrchestrationMetrics()
        for stage, result in context.stages.items():
            if result.duration_ms is not None:
                metrics.stage_durations[stage.value] = result.duration_ms
            if result.status == StageStatus.COMPLETED:
                metrics.success_count += 1
            elif result.status == StageStatus.FAILED:
                metrics.failure_count += 1
            elif result.status == StageStatus.SKIPPED:
                metrics.skip_count += 1
            metrics.retry_count += result.retry_count

        if context.started_at and context.completed_at:
            metrics.pipeline_duration_ms = (
                context.completed_at - context.started_at
            ).total_seconds() * 1000

        checkpoints = getattr(context, "checkpoint", None)
        if checkpoints is not None:
            metrics.checkpoint_count = 1

        return metrics
