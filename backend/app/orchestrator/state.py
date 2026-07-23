from __future__ import annotations

from app.orchestrator.schemas import OrchestrationContext, OrchestratorState, PipelineStage


class OrchestrationStateManager:
    def set_running(self, context: OrchestrationContext) -> OrchestrationContext:
        context.state = OrchestratorState.RUNNING
        return context

    def set_completed(self, context: OrchestrationContext) -> OrchestrationContext:
        context.state = OrchestratorState.COMPLETED
        context.completed_at = __import__("datetime").datetime.utcnow()
        return context

    def set_failed(self, context: OrchestrationContext, error: str) -> OrchestrationContext:
        context.state = OrchestratorState.FAILED
        context.completed_at = __import__("datetime").datetime.utcnow()
        context.errors.append(error)
        return context

    def set_cancelled(self, context: OrchestrationContext, reason: str = "") -> OrchestrationContext:
        context.state = OrchestratorState.CANCELLED
        context.completed_at = __import__("datetime").datetime.utcnow()
        if reason:
            context.warnings.append(reason)
        return context

    def set_current_stage(self, context: OrchestrationContext, stage: PipelineStage) -> OrchestrationContext:
        context.current_stage = stage
        return context

    def is_running(self, context: OrchestrationContext) -> bool:
        return context.state == OrchestratorState.RUNNING

    def is_completed(self, context: OrchestrationContext) -> bool:
        return context.state in (OrchestratorState.COMPLETED, OrchestratorState.FAILED, OrchestratorState.CANCELLED)

    def can_resume(self, context: OrchestrationContext) -> bool:
        return context.state in (OrchestratorState.FAILED, OrchestratorState.PAUSED)
