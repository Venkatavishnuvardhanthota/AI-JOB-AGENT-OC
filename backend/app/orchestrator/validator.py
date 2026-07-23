from __future__ import annotations

from app.orchestrator.config import OrchestratorConfig
from app.orchestrator.exceptions import ValidationError
from app.orchestrator.schemas import ExecutionMode, OrchestrationContext


class OrchestratorValidator:
    def __init__(self, config: OrchestratorConfig) -> None:
        self._config = config

    def validate_mode(self, mode: ExecutionMode | str) -> ExecutionMode:
        if isinstance(mode, str):
            try:
                mode = ExecutionMode(mode)
            except ValueError:
                raise ValidationError(f"Unknown execution mode: {mode}") from None
        if mode.value not in self._config.allowed_execution_modes:
            raise ValidationError(f"Execution mode '{mode.value}' is not allowed")
        return mode

    def validate_context(self, context: OrchestrationContext) -> list[str]:
        issues: list[str] = []
        if context.job is None and context.execution_mode != ExecutionMode.MANUAL:
            pass
        if context.profile is None and context.execution_mode != ExecutionMode.MANUAL:
            pass
        return issues

    def validate_stage_input(self, stage_name: str, inputs: dict) -> list[str]:
        return []
