from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from app.operations.config import OperationsConfig
from app.operations.diagnostics import OperationsDiagnosticsEngine
from app.operations.exceptions import (
    DiagnosticsError,
    ExportError,
    HealthCheckError,
    HistoryError,
    LoggingError,
    MetricsError,
    OperationsError,
    ReportError,
    TracingError,
)
from app.operations.export import OperationsExporter
from app.operations.health import OperationsHealthChecker
from app.operations.history import OperationsExecutionHistory
from app.operations.logger import OperationsStructuredLogger
from app.operations.metrics import OperationsMetricsCollector
from app.operations.reporting import OperationsReportGenerator
from app.operations.schemas import (
    DiagnosticFinding,
    ExecutionReport,
    FailureReport,
    HealthCheckResult,
    HealthStatus,
    HistoryEntry,
    PerformanceReport,
    ProviderReport,
    SystemSummary,
    TraceEntry,
    UsageReport,
)
from app.operations.service import OperationsService
from app.operations.tracing import OperationsTracer


@pytest.fixture
def config() -> OperationsConfig:
    return OperationsConfig(
        metrics_buffer_size=100,
        max_trace_entries=100,
        slow_stage_threshold_ms=100.0,
        high_retry_threshold=2,
        history_retention_days=30,
        export_dir=tempfile.mkdtemp(),
    )


@pytest.fixture
def service(config: OperationsConfig) -> OperationsService:
    return OperationsService(config=config)


@pytest.fixture
def tracer(config: OperationsConfig) -> OperationsTracer:
    return OperationsTracer(config)


@pytest.fixture
def metrics(config: OperationsConfig) -> OperationsMetricsCollector:
    return OperationsMetricsCollector(config)


@pytest.fixture
def health(config: OperationsConfig) -> OperationsHealthChecker:
    return OperationsHealthChecker(config)


@pytest.fixture
def diagnostics(config: OperationsConfig) -> OperationsDiagnosticsEngine:
    return OperationsDiagnosticsEngine(config)


@pytest.fixture
def history(config: OperationsConfig) -> OperationsExecutionHistory:
    return OperationsExecutionHistory(config)


@pytest.fixture
def reporting(config: OperationsConfig) -> OperationsReportGenerator:
    return OperationsReportGenerator(config)


@pytest.fixture
def exporter(config: OperationsConfig) -> OperationsExporter:
    return OperationsExporter(config)


# --- Exception Tests ---


class TestExceptions:
    def test_exception_hierarchy(self):
        assert issubclass(LoggingError, OperationsError)
        assert issubclass(TracingError, OperationsError)
        assert issubclass(MetricsError, OperationsError)
        assert issubclass(HealthCheckError, OperationsError)
        assert issubclass(DiagnosticsError, OperationsError)
        assert issubclass(HistoryError, OperationsError)
        assert issubclass(ReportError, OperationsError)
        assert issubclass(ExportError, OperationsError)

    def test_exceptions_instantiate(self):
        assert isinstance(LoggingError("fail"), LoggingError)
        assert isinstance(TracingError("fail"), TracingError)


# --- Schema Tests ---


class TestSchemas:
    def test_trace_entry_defaults(self):
        e = TraceEntry(span_id="s1", trace_id="t1", name="test")
        assert e.span_id == "s1"
        assert e.trace_id == "t1"
        assert e.parent_id is None
        assert e.duration_ms is None

    def test_health_check_result_defaults(self):
        r = HealthCheckResult(component="db", status=HealthStatus.HEALTHY)
        assert r.component == "db"
        assert r.status == HealthStatus.HEALTHY

    def test_diagnostic_finding_defaults(self):
        f = DiagnosticFinding(severity="error", category="test", message="test")
        assert f.finding_id is not None
        assert f.details == {}

    def test_history_entry_defaults(self):
        e = HistoryEntry(orchestration_id="o1", event_type="run", state="completed")
        assert e.entry_id is not None
        assert e.resume_count == 0
        assert e.retry_count == 0

    def test_execution_report_defaults(self):
        r = ExecutionReport(orchestration_id="o1", state="ok", execution_mode="single")
        assert r.stages_completed == 0
        assert r.errors == []

    def test_performance_report_defaults(self):
        r = PerformanceReport(period_start=datetime.utcnow(), period_end=datetime.utcnow())
        assert r.total_orchestrations == 0

    def test_provider_report_defaults(self):
        r = ProviderReport(provider="openai")
        assert r.total_requests == 0

    def test_usage_report_defaults(self):
        r = UsageReport()
        assert r.total_ai_requests == 0
        assert r.total_tokens == 0

    def test_failure_report_defaults(self):
        r = FailureReport()
        assert r.total_failures == 0

    def test_system_summary_defaults(self):
        r = SystemSummary()
        assert r.total_orchestrations == 0


# --- Logger Tests ---


class TestStructuredLogger:
    def test_log_debug(self, config):
        logger = OperationsStructuredLogger(config)
        logger.debug("test debug", module="test", correlation_id="c1")
        # No exception = success

    def test_log_info(self, config):
        logger = OperationsStructuredLogger(config)
        logger.info("test info", module="test", correlation_id="c1")

    def test_log_warning(self, config):
        logger = OperationsStructuredLogger(config)
        logger.warning("test warning", module="test")

    def test_log_error(self, config):
        logger = OperationsStructuredLogger(config)
        logger.error("test error", exception="ValueError: fail")

    def test_log_critical(self, config):
        logger = OperationsStructuredLogger(config)
        logger.critical("test critical")

    def test_log_all_fields(self, config):
        logger = OperationsStructuredLogger(config)
        logger.info(
            "full message",
            module="test_module",
            component="test_component",
            correlation_id="corr_1",
            orchestration_id="orch_1",
            application_id="app_1",
            provider="openai",
            stage="job_matching",
            duration=1500.0,
            extra_field="value",
        )


# --- Tracing Tests ---


class TestTracing:
    def test_start_and_end_span(self, tracer):
        span_id = tracer.start_span("test_span", "trace_1")
        assert span_id is not None
        tracer.end_span(span_id)

    def test_get_trace(self, tracer):
        span_id = tracer.start_span("test_span", "trace_1")
        tracer.end_span(span_id)
        trace = tracer.get_trace("trace_1")
        assert trace is not None
        assert len(trace) == 1
        assert trace[0]["name"] == "test_span"
        assert trace[0]["duration_ms"] is not None

    def test_get_nonexistent_trace(self, tracer):
        trace = tracer.get_trace("nonexistent")
        assert trace is None

    def test_span_with_parent(self, tracer):
        parent = tracer.start_span("parent", "trace_2")
        child = tracer.start_span("child", "trace_2", parent_id=parent)
        tracer.end_span(child)
        tracer.end_span(parent)
        trace = tracer.get_trace("trace_2")
        assert len(trace) == 2

    def test_span_with_tags(self, tracer):
        span_id = tracer.start_span("tagged", "trace_3", stage="test", provider="ai")
        tracer.end_span(span_id, result="ok")
        trace = tracer.get_trace("trace_3")
        assert trace[0]["tags"]["stage"] == "test"

    def test_end_nonexistent_span(self, tracer):
        with pytest.raises(TracingError):
            tracer.end_span("nonexistent")

    def test_max_entries(self, config):
        config.max_trace_entries = 2
        small_tracer = OperationsTracer(config)
        small_tracer.start_span("s1", "trace_max")
        small_tracer.start_span("s2", "trace_max")
        with pytest.raises(TracingError):
            small_tracer.start_span("s3", "trace_max")


# --- Metrics Tests ---


class TestMetricsCollector:
    def test_increment(self, metrics):
        metrics.increment("test.counter")
        snapshot = metrics.get_metrics_snapshot()
        assert snapshot["counters"]["test.counter"] == 1.0

    def test_increment_multiple(self, metrics):
        metrics.increment("test.counter", 5.0)
        snapshot = metrics.get_metrics_snapshot()
        assert snapshot["counters"]["test.counter"] == 5.0

    def test_increment_with_tags(self, metrics):
        metrics.increment("test.counter", 1.0, stage="match", provider="ai")
        snapshot = metrics.get_metrics_snapshot()
        assert any("stage=match" in k for k in snapshot["counters"])

    def test_gauge(self, metrics):
        metrics.gauge("test.gauge", 42.0)
        snapshot = metrics.get_metrics_snapshot()
        assert snapshot["gauges"]["test.gauge"] == 42.0

    def test_gauge_update(self, metrics):
        metrics.gauge("test.gauge", 10.0)
        metrics.gauge("test.gauge", 20.0)
        snapshot = metrics.get_metrics_snapshot()
        assert snapshot["gauges"]["test.gauge"] == 20.0

    def test_timing(self, metrics):
        metrics.timing("test.timing", 150.0)
        snapshot = metrics.get_metrics_snapshot()
        assert "test.timing" in snapshot["timings"]
        assert snapshot["timings"]["test.timing"]["avg"] == 150.0

    def test_timing_multiple(self, metrics):
        metrics.timing("test.timing", 100.0)
        metrics.timing("test.timing", 200.0)
        snapshot = metrics.get_metrics_snapshot()
        assert snapshot["timings"]["test.timing"]["count"] == 2
        assert snapshot["timings"]["test.timing"]["avg"] == 150.0

    def test_metrics_snapshot_structure(self, metrics):
        snapshot = metrics.get_metrics_snapshot()
        assert "counters" in snapshot
        assert "gauges" in snapshot
        assert "timings" in snapshot
        assert "total_points" in snapshot


# --- Health Tests ---


class TestHealthChecker:
    def test_check_application(self, health):
        result = health.check_application()
        assert result["status"] == "healthy"
        assert result["component"] == "application"

    def test_check_database_healthy(self, health):
        with patch("app.core.config.settings", DATABASE_URL="postgresql://localhost:5432/db"):
            result = health.check_database()
            assert result["status"] == "healthy"

    def test_check_database_degraded(self, health):
        with patch("app.core.config.settings", DATABASE_URL=""):
            result = health.check_database()
            assert result["status"] == "degraded"

    def test_check_ai_provider_healthy(self, health):
        with patch("app.ai.dependencies.get_ai_service") as mock_svc:
            mock_svc.return_value.provider_manager.get_available_providers.return_value = ["openai"]
            result = health.check_ai_provider()
            assert result["status"] == "healthy"

    def test_check_ai_provider_degraded(self, health):
        with patch("app.ai.dependencies.get_ai_service") as mock_svc:
            mock_svc.return_value.provider_manager.get_available_providers.return_value = []
            result = health.check_ai_provider()
            assert result["status"] == "degraded"

    def test_check_ai_provider_unhealthy(self, health):
        with patch("app.ai.dependencies.get_ai_service", side_effect=Exception("Service down")):
            result = health.check_ai_provider()
            assert result["status"] == "unhealthy"

    def test_check_orchestrator_healthy(self, health):
        result = health.check_orchestrator()
        assert result["status"] == "healthy"

    def test_check_all_healthy(self, health):
        with (
            patch("app.core.config.settings", DATABASE_URL="postgresql://localhost:5432/db"),
            patch("app.ai.dependencies.get_ai_service") as mock_svc,
        ):
            mock_svc.return_value.provider_manager.get_available_providers.return_value = ["openai"]
            result = health.check_all()
            assert result["overall"] == "healthy"

    def test_check_all_degraded(self, health):
        with (
            patch("app.core.config.settings", DATABASE_URL=""),
            patch("app.ai.dependencies.get_ai_service") as mock_svc,
        ):
            mock_svc.return_value.provider_manager.get_available_providers.return_value = ["openai"]
            result = health.check_all()
            assert result["overall"] == "degraded"


# --- Diagnostics Tests ---


class TestDiagnostics:
    def test_no_findings(self, diagnostics):
        findings = diagnostics.analyze({"stages": {}, "errors": []})
        assert findings == []

    def test_slow_stage(self, diagnostics):
        context = {
            "stages": {
                "job_matching": {"duration_ms": 50000, "retry_count": 0},
            },
            "errors": [],
        }
        findings = diagnostics.analyze(context)
        slow = [f for f in findings if f["category"] == "slow_stage"]
        assert len(slow) == 1
        assert slow[0]["severity"] == "warning"

    def test_normal_stage_not_reported(self, diagnostics):
        context = {
            "stages": {
                "job_matching": {"duration_ms": 50, "retry_count": 0},
            },
            "errors": [],
        }
        findings = diagnostics.analyze(context)
        slow = [f for f in findings if f["category"] == "slow_stage"]
        assert len(slow) == 0

    def test_high_retry(self, diagnostics):
        context = {
            "stages": {
                "upload": {"duration_ms": 100, "retry_count": 3},
            },
            "errors": [],
        }
        findings = diagnostics.analyze(context)
        retry_findings = [f for f in findings if f["category"] == "high_retry_rate"]
        assert len(retry_findings) == 1

    def test_ai_failures(self, diagnostics):
        context = {
            "stages": {},
            "errors": ["AI provider timeout", "network error"],
        }
        findings = diagnostics.analyze(context)
        ai_findings = [f for f in findings if f["category"] == "ai_failure"]
        assert len(ai_findings) == 1

    def test_pipeline_bottleneck(self, diagnostics):
        context = {
            "stages": {
                "job_matching": {"duration_ms": 50000, "retry_count": 0},
                "profile": {"duration_ms": 100, "retry_count": 0},
                "upload": {"duration_ms": 200, "retry_count": 0},
            },
            "errors": [],
        }
        findings = diagnostics.analyze(context)
        bottleneck = [f for f in findings if f["category"] == "pipeline_bottleneck"]
        assert len(bottleneck) == 1

    def test_repeated_failures(self, diagnostics):
        context = {
            "stages": {},
            "errors": ["timeout", "timeout", "timeout"],
        }
        findings = diagnostics.analyze(context)
        repeated = [f for f in findings if f["category"] == "repeated_failure"]
        assert len(repeated) == 1


# --- History Tests ---


class TestExecutionHistory:
    def test_record_and_query(self, history):
        history.record(
            {
                "orchestration_id": "o1",
                "event_type": "run",
                "state": "completed",
            }
        )
        results = history.query()
        assert len(results) == 1
        assert results[0]["orchestration_id"] == "o1"

    def test_query_by_orchestration_id(self, history):
        history.record({"orchestration_id": "o1", "event_type": "run", "state": "completed"})
        history.record({"orchestration_id": "o2", "event_type": "run", "state": "failed"})
        results = history.query({"orchestration_id": "o1"})
        assert len(results) == 1
        assert results[0]["orchestration_id"] == "o1"

    def test_query_by_state(self, history):
        history.record({"orchestration_id": "o1", "event_type": "run", "state": "completed"})
        history.record({"orchestration_id": "o2", "event_type": "run", "state": "failed"})
        results = history.query({"state": "failed"})
        assert len(results) == 1

    def test_query_by_event_type(self, history):
        history.record({"orchestration_id": "o1", "event_type": "run", "state": "completed"})
        history.record({"orchestration_id": "o1", "event_type": "resume", "state": "running"})
        results = history.query({"event_type": "resume"})
        assert len(results) == 1

    def test_query_since(self, history):
        history.record(
            {
                "orchestration_id": "o1",
                "event_type": "run",
                "state": "completed",
                "started_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            }
        )
        history.record(
            {
                "orchestration_id": "o2",
                "event_type": "run",
                "state": "completed",
                "started_at": datetime.utcnow().isoformat(),
            }
        )
        results = history.query({"since": datetime.utcnow() - timedelta(hours=1)})
        assert len(results) == 1

    def test_record_failure(self, history):
        history.record(
            {
                "orchestration_id": "o1",
                "event_type": "run",
                "state": "failed",
                "error": "timeout",
                "warnings": ["slow"],
            }
        )
        results = history.query({"state": "failed"})
        assert results[0]["error"] == "timeout"

    def test_prune_old_entries(self, config):
        config.history_retention_days = 0
        hist = OperationsExecutionHistory(config)
        hist.record({"orchestration_id": "o1", "event_type": "run", "state": "completed"})
        results = hist.query()
        assert len(results) == 1


# --- Reporting Tests ---


class TestReportGenerator:
    def test_execution_report(self, reporting):
        data = {
            "orchestration_id": "o1",
            "state": "completed",
            "execution_mode": "single",
            "stages": {
                "job_matching": {"status": "completed", "retry_count": 0},
                "upload": {"status": "failed", "retry_count": 2},
                "cover_letter": {"status": "skipped", "retry_count": 0},
            },
            "errors": ["upload failed"],
            "warnings": [],
        }
        report = reporting.generate("execution", data)
        assert report["orchestration_id"] == "o1"
        assert report["stages_completed"] == 1
        assert report["stages_failed"] == 1
        assert report["stages_skipped"] == 1

    def test_performance_report(self, reporting):
        data = {
            "period_start": datetime.utcnow() - timedelta(days=1),
            "period_end": datetime.utcnow(),
            "total_orchestrations": 100,
            "success_count": 85,
            "failure_count": 15,
            "avg_duration_ms": 5000.0,
            "stage_durations": {
                "job_matching": 10000.0,
                "upload": 500.0,
                "profile": 200.0,
            },
        }
        report = reporting.generate("performance", data)
        assert report["total_orchestrations"] == 100
        assert len(report["top_slow_stages"]) == 3

    def test_provider_report(self, reporting):
        data = {
            "provider": "openai",
            "total_requests": 200,
            "success_count": 190,
            "failure_count": 10,
            "avg_latency_ms": 1500.0,
        }
        report = reporting.generate("provider", data)
        assert report["provider"] == "openai"
        assert report["error_rate"] == 5.0

    def test_provider_report_no_requests(self, reporting):
        data = {
            "provider": "openai",
            "total_requests": 0,
            "success_count": 0,
            "failure_count": 0,
        }
        report = reporting.generate("provider", data)
        assert report["error_rate"] is None

    def test_usage_report(self, reporting):
        data = {
            "total_ai_requests": 50,
            "total_tokens": 150000,
            "estimated_cost": 0.75,
            "model_breakdown": {"gpt-4": {"requests": 30, "tokens": 100000}},
        }
        report = reporting.generate("usage", data)
        assert report["total_ai_requests"] == 50

    def test_failure_report(self, reporting):
        data = {
            "total_failures": 10,
            "failures_by_stage": {"upload": 5, "submission": 5},
            "failures_by_error": {"timeout": 7, "auth": 3},
            "top_failures": [{"stage": "upload", "error": "timeout"}],
        }
        report = reporting.generate("failure", data)
        assert report["total_failures"] == 10

    def test_system_summary(self, reporting):
        data = {
            "uptime_hours": 72.0,
            "total_orchestrations": 500,
            "total_failures": 25,
            "active_orchestrations": 3,
            "total_ai_requests": 2000,
            "total_browser_actions": 1500,
            "total_uploads": 400,
            "total_submissions": 350,
        }
        report = reporting.generate("system", data)
        assert report["total_orchestrations"] == 500
        assert report["error_rate"] == 5.0

    def test_unknown_report_type(self, reporting):
        with pytest.raises(ReportError):
            reporting.generate("unknown", {})


# --- Export Tests ---


class TestExporter:
    def test_export_json(self, exporter):
        path = exporter.export_json({"key": "value"}, "test_export")
        assert path.endswith(".json")
        assert os.path.isfile(path)
        with open(path) as f:
            assert json.load(f) == {"key": "value"}

    def test_export_csv(self, exporter):
        data = [{"name": "Alice", "score": 95}, {"name": "Bob", "score": 87}]
        path = exporter.export_csv(data, "test_export")
        assert path.endswith(".csv")
        assert os.path.isfile(path)
        with open(path) as f:
            content = f.read()
            assert "Alice" in content
            assert "Bob" in content

    def test_export_csv_empty(self, exporter):
        with pytest.raises(ExportError):
            exporter.export_csv([], "empty")

    def test_export_pdf_no_library(self, exporter):
        with pytest.raises(ExportError, match="requires 'weasyprint'"):
            exporter.export_pdf("<html></html>", "test")


# --- Service Tests ---


class TestOperationsService:
    def test_log_delegation(self, service):
        service.debug("test", module="svc")
        service.info("test", module="svc")
        service.warning("test", module="svc")
        service.error("test", module="svc")
        service.critical("test", module="svc")

    def test_tracing_delegation(self, service):
        span_id = service.start_span("test", "trace_svc")
        service.end_span(span_id)
        trace = service.get_trace("trace_svc")
        assert trace is not None
        assert len(trace) == 1

    def test_metrics_delegation(self, service):
        service.increment("test.counter")
        service.gauge("test.gauge", 42.0)
        service.timing("test.timing", 100.0)
        snapshot = service.get_metrics_snapshot()
        assert snapshot["counters"]["test.counter"] == 1.0

    def test_health_delegation(self, service):
        result = service.check_application()
        assert result["status"] == "healthy"

    def test_diagnostics_delegation(self, service):
        findings = service.analyze({"stages": {}, "errors": []})
        assert findings == []

    def test_history_delegation(self, service):
        service.record_history(
            {
                "orchestration_id": "o1",
                "event_type": "run",
                "state": "completed",
            }
        )
        results = service.query_history()
        assert len(results) == 1

    def test_reporting_delegation(self, service):
        report = service.generate_report(
            "execution",
            {
                "orchestration_id": "o1",
                "state": "completed",
                "execution_mode": "single",
                "stages": {},
                "errors": [],
                "warnings": [],
            },
        )
        assert report["orchestration_id"] == "o1"

    def test_export_json_delegation(self, service):
        path = service.export_json({"key": "value"}, "svc_export")
        assert os.path.isfile(path)

    def test_export_csv_delegation(self, service):
        path = service.export_csv([{"col": "val"}], "svc_csv")
        assert os.path.isfile(path)

    def test_record_orchestration_event(self, service):
        service.record_orchestration_event(
            orchestration_id="o1",
            event_type="run",
            state="completed",
            duration_ms=5000.0,
        )
        results = service.query_history({"orchestration_id": "o1"})
        assert len(results) == 1
        assert results[0]["duration_ms"] == 5000.0

    def test_record_stage_metrics(self, service):
        service.record_stage_metrics("job_matching", 1500.0, "completed", retry_count=2)
        snapshot = service.get_metrics_snapshot()
        timing_key = [k for k in snapshot["timings"] if "stage.job_matching.duration" in k]
        assert len(timing_key) > 0
        counter_key = [k for k in snapshot["counters"] if "stage.job_matching" in k]
        assert len(counter_key) > 0

    def test_get_trace_nonexistent(self, service):
        trace = service.get_trace("nonexistent")
        assert trace is None

    def test_check_all_delegation(self, service):
        result = service.check_all()
        assert "overall" in result
        assert "checks" in result
