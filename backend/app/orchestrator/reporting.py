from __future__ import annotations

from app.orchestrator.interfaces import ReportBuilder
from app.orchestrator.metrics import OrchestratorMetricsCollector
from app.orchestrator.schemas import OrchestrationContext, OrchestrationReport


class OrchestrationReportBuilder(ReportBuilder):
    def __init__(self, metrics_collector: OrchestratorMetricsCollector) -> None:
        self._metrics = metrics_collector

    def build(self, context: OrchestrationContext) -> OrchestrationReport:
        stages_dict = {}
        for stage, result in context.stages.items():
            stages_dict[stage.value] = result

        retry_history = list(getattr(context, "_retry_history", []))

        report = OrchestrationReport(
            orchestration_id=context.orchestration_id,
            state=context.state,
            execution_mode=context.execution_mode,
            stages=stages_dict,
            metrics=self._metrics.get_metrics(context),
            errors=context.errors,
            warnings=context.warnings,
            started_at=context.started_at,
            completed_at=context.completed_at,
        )

        if context.started_at and context.completed_at:
            report.total_duration_ms = (
                context.completed_at - context.started_at
            ).total_seconds() * 1000

        report.retry_history = retry_history

        checkpoints_created = 0
        for result in context.stages.values():
            if result.checkpoint_id:
                checkpoints_created += 1
        report.checkpoints_created = checkpoints_created

        return report
