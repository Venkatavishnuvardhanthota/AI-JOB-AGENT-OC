from __future__ import annotations

from typing import Any

import structlog

from app.operations.config import OperationsConfig
from app.operations.diagnostics import OperationsDiagnosticsEngine
from app.operations.export import OperationsExporter
from app.operations.health import OperationsHealthChecker
from app.operations.history import OperationsExecutionHistory
from app.operations.logger import OperationsStructuredLogger
from app.operations.metrics import OperationsMetricsCollector
from app.operations.reporting import OperationsReportGenerator
from app.operations.tracing import OperationsTracer

logger = structlog.get_logger(__name__)


class OperationsService:
    def __init__(self, config: OperationsConfig | None = None) -> None:
        self._config = config or OperationsConfig()
        self._logger = OperationsStructuredLogger(self._config)
        self._tracer = OperationsTracer(self._config)
        self._metrics = OperationsMetricsCollector(self._config)
        self._health = OperationsHealthChecker(self._config)
        self._diagnostics = OperationsDiagnosticsEngine(self._config)
        self._history = OperationsExecutionHistory(self._config)
        self._reporting = OperationsReportGenerator(self._config)
        self._exporter = OperationsExporter(self._config)

    # --- Logger ---

    @property
    def log(self) -> OperationsStructuredLogger:
        return self._logger

    def debug(self, message: str, **kwargs: Any) -> None:
        self._logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        self._logger.critical(message, **kwargs)

    # --- Tracing ---

    def start_span(self, name: str, trace_id: str, parent_id: str | None = None, **tags: Any) -> str:
        return self._tracer.start_span(name, trace_id, parent_id, **tags)

    def end_span(self, span_id: str, **tags: Any) -> None:
        self._tracer.end_span(span_id, **tags)

    def get_trace(self, trace_id: str) -> list[dict[str, Any]] | None:
        return self._tracer.get_trace(trace_id)

    # --- Metrics ---

    def increment(self, name: str, value: float = 1.0, **tags: Any) -> None:
        self._metrics.increment(name, value, **tags)

    def gauge(self, name: str, value: float, **tags: Any) -> None:
        self._metrics.gauge(name, value, **tags)

    def timing(self, name: str, duration_ms: float, **tags: Any) -> None:
        self._metrics.timing(name, duration_ms, **tags)

    def get_metrics_snapshot(self) -> dict[str, Any]:
        return self._metrics.get_metrics_snapshot()

    # --- Health ---

    def check_application(self) -> dict[str, Any]:
        return self._health.check_application()

    def check_database(self) -> dict[str, Any]:
        return self._health.check_database()

    def check_ai_provider(self) -> dict[str, Any]:
        return self._health.check_ai_provider()

    def check_orchestrator(self) -> dict[str, Any]:
        return self._health.check_orchestrator()

    def check_all(self) -> dict[str, Any]:
        return self._health.check_all()

    # --- Diagnostics ---

    def analyze(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        return self._diagnostics.analyze(context)

    # --- History ---

    def record_history(self, entry: dict[str, Any]) -> None:
        self._history.record(entry)

    def query_history(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self._history.query(filters)

    # --- Reporting ---

    def generate_report(self, report_type: str, data: dict[str, Any]) -> dict[str, Any]:
        return self._reporting.generate(report_type, data)

    # --- Export ---

    def export_json(self, data: Any, path: str) -> str:
        return self._exporter.export_json(data, path)

    def export_csv(self, data: list[dict[str, Any]], path: str) -> str:
        return self._exporter.export_csv(data, path)

    def export_pdf(self, html_content: str, path: str) -> str:
        return self._exporter.export_pdf(html_content, path)

    # --- Convenience ---

    def record_orchestration_event(
        self,
        orchestration_id: str,
        event_type: str,
        state: str,
        duration_ms: float | None = None,
        error: str | None = None,
        warnings: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        entry = {
            "orchestration_id": orchestration_id,
            "event_type": event_type,
            "state": state,
            "duration_ms": duration_ms,
            "error": error,
            "warnings": warnings or [],
            **kwargs,
        }
        self._history.record(entry)

    def record_stage_metrics(
        self,
        stage: str,
        duration_ms: float,
        status: str,
        retry_count: int = 0,
    ) -> None:
        self._metrics.timing(f"stage.{stage}.duration", duration_ms, stage=stage)
        self._metrics.increment(f"stage.{stage}.{status}", 1.0, stage=stage)
        if retry_count > 0:
            self._metrics.increment(f"stage.{stage}.retries", retry_count, stage=stage)
