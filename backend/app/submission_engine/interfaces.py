from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.submission_engine.schemas import (
    ConfirmationResult,
    ExecutionMetrics,
    StepExecution,
    SubmissionReport,
    SubmissionStatus,
)


class SubmissionProvider(ABC):
    @abstractmethod
    def supports(self, url: str) -> bool: ...

    @abstractmethod
    def submit(self, page: Any, timeout_ms: float) -> bool: ...

    @abstractmethod
    def confirm(self, page: Any, timeout_ms: float) -> ConfirmationResult: ...


class FieldExecutor(ABC):
    @abstractmethod
    def execute_step(self, page: Any, step: Any) -> StepExecution: ...

    @abstractmethod
    def execute_plan(self, page: Any, execution_plan: Any) -> list[StepExecution]: ...


class SubmissionOrchestrator(ABC):
    @abstractmethod
    def run(
        self,
        page: Any,
        execution_plan: Any,
        upload_plan: Any | None = None,
        upload_service: Any | None = None,
        mode: Any = None,
        provider: Any | None = None,
    ) -> SubmissionReport: ...


class SubmissionValidator(ABC):
    @abstractmethod
    def validate(self, page: Any, execution_plan: Any, upload_plan: Any | None = None) -> list[str]: ...


class SubmissionConfirmer(ABC):
    @abstractmethod
    def confirm(self, page: Any, timeout_ms: float) -> ConfirmationResult: ...


class SubmissionRecovery(ABC):
    @abstractmethod
    def can_retry(self, error: str, attempt: int) -> bool: ...

    @abstractmethod
    def recover(self, page: Any, error: str, attempt: int) -> bool: ...


class SafetyGuard(ABC):
    @abstractmethod
    def check(self, execution_mode: Any) -> list[Any]: ...

    @abstractmethod
    def allow_submit(self) -> bool: ...


class MetricsTracker(ABC):
    @abstractmethod
    def record_step(self, step: StepExecution) -> None: ...

    @abstractmethod
    def get_metrics(self) -> ExecutionMetrics: ...


class ReportGenerator(ABC):
    @abstractmethod
    def generate(self, status: SubmissionStatus) -> SubmissionReport: ...
