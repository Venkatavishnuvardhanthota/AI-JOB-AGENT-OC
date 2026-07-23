from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StructuredLogger(ABC):
    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None: ...

    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None: ...


class Tracer(ABC):
    @abstractmethod
    def start_span(self, name: str, trace_id: str, parent_id: str | None = None, **tags: Any) -> str: ...

    @abstractmethod
    def end_span(self, span_id: str, **tags: Any) -> None: ...

    @abstractmethod
    def get_trace(self, trace_id: str) -> list[dict[str, Any]] | None: ...


class MetricsCollector(ABC):
    @abstractmethod
    def increment(self, name: str, value: float = 1.0, **tags: Any) -> None: ...

    @abstractmethod
    def gauge(self, name: str, value: float, **tags: Any) -> None: ...

    @abstractmethod
    def timing(self, name: str, duration_ms: float, **tags: Any) -> None: ...

    @abstractmethod
    def get_metrics_snapshot(self) -> dict[str, Any]: ...


class HealthChecker(ABC):
    @abstractmethod
    def check_application(self) -> dict[str, Any]: ...

    @abstractmethod
    def check_database(self) -> dict[str, Any]: ...

    @abstractmethod
    def check_ai_provider(self) -> dict[str, Any]: ...

    @abstractmethod
    def check_all(self) -> dict[str, Any]: ...


class DiagnosticsEngine(ABC):
    @abstractmethod
    def analyze(self, context: dict[str, Any]) -> list[dict[str, Any]]: ...


class ExecutionHistory(ABC):
    @abstractmethod
    def record(self, entry: dict[str, Any]) -> None: ...

    @abstractmethod
    def query(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]: ...


class ReportGenerator(ABC):
    @abstractmethod
    def generate(self, report_type: str, data: dict[str, Any]) -> Any: ...


class Exporter(ABC):
    @abstractmethod
    def export_json(self, data: Any, path: str) -> str: ...

    @abstractmethod
    def export_csv(self, data: list[dict[str, Any]], path: str) -> str: ...

    @abstractmethod
    def export_pdf(self, html_content: str, path: str) -> str: ...
