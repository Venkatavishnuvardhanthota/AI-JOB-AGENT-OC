from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.orchestrator.schemas import (
    CheckpointData,
    OrchestrationContext,
    PipelineStage,
    RecoveryStrategy,
)


class PipelineStageExecutor(ABC):
    @abstractmethod
    def stage(self) -> PipelineStage: ...

    @abstractmethod
    def is_skippable(self) -> bool: ...

    @abstractmethod
    def should_skip(self, context: OrchestrationContext) -> bool: ...

    @abstractmethod
    def execute(self, context: OrchestrationContext) -> OrchestrationContext: ...


class CheckpointStore(ABC):
    @abstractmethod
    def save(self, checkpoint: CheckpointData) -> None: ...

    @abstractmethod
    def load(self, checkpoint_id: str) -> CheckpointData | None: ...

    @abstractmethod
    def list_for(self, orchestration_id: str) -> list[CheckpointData]: ...


class RecoveryStrategyExecutor(ABC):
    @abstractmethod
    def determine_strategy(
        self,
        context: OrchestrationContext,
        stage: PipelineStage,
        error: str,
        attempt: int,
    ) -> RecoveryStrategy: ...

    @abstractmethod
    def execute_strategy(
        self,
        context: OrchestrationContext,
        stage: PipelineStage,
        strategy: RecoveryStrategy,
        error: str,
        attempt: int,
    ) -> OrchestrationContext: ...


class OrchestrationDispatcher(ABC):
    @abstractmethod
    def dispatch(self, context: OrchestrationContext) -> OrchestrationContext: ...


class MetricsCollector(ABC):
    @abstractmethod
    def record_stage_start(self, stage: PipelineStage, context: OrchestrationContext) -> None: ...

    @abstractmethod
    def record_stage_end(self, stage: PipelineStage, context: OrchestrationContext) -> None: ...

    @abstractmethod
    def get_metrics(self, context: OrchestrationContext) -> Any: ...


class ReportBuilder(ABC):
    @abstractmethod
    def build(self, context: OrchestrationContext) -> Any: ...
