from __future__ import annotations

from datetime import datetime
from typing import Any

from app.operations.config import OperationsConfig
from app.operations.exceptions import ReportError
from app.operations.interfaces import ReportGenerator
from app.operations.schemas import (
    ExecutionReport,
    FailureReport,
    PerformanceReport,
    ProviderReport,
    SystemSummary,
    UsageReport,
)


class OperationsReportGenerator(ReportGenerator):
    def __init__(self, config: OperationsConfig) -> None:
        self._config = config

    def generate(self, report_type: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            if report_type == "execution":
                return self._execution_report(data)
            if report_type == "performance":
                return self._performance_report(data)
            if report_type == "provider":
                return self._provider_report(data)
            if report_type == "usage":
                return self._usage_report(data)
            if report_type == "failure":
                return self._failure_report(data)
            if report_type == "system":
                return self._system_summary(data)
            raise ReportError(f"Unknown report type: {report_type}")
        except Exception as e:
            raise ReportError(f"Report generation failed: {e}") from e

    def _execution_report(self, data: dict[str, Any]) -> dict[str, Any]:
        stages = data.get("stages", {})
        return ExecutionReport(
            orchestration_id=data.get("orchestration_id", ""),
            state=data.get("state", "unknown"),
            execution_mode=data.get("execution_mode", "unknown"),
            total_duration_ms=data.get("total_duration_ms"),
            stages_completed=sum(1 for s in stages.values() if isinstance(s, dict) and s.get("status") == "completed"),
            stages_failed=sum(1 for s in stages.values() if isinstance(s, dict) and s.get("status") == "failed"),
            stages_skipped=sum(1 for s in stages.values() if isinstance(s, dict) and s.get("status") == "skipped"),
            retry_count=sum(s.get("retry_count", 0) for s in stages.values() if isinstance(s, dict)),
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
        ).model_dump()

    def _performance_report(self, data: dict[str, Any]) -> dict[str, Any]:
        durations = data.get("stage_durations", {})
        sorted_stages = sorted(durations.items(), key=lambda x: x[1], reverse=True) if durations else []
        return PerformanceReport(
            period_start=data.get("period_start", datetime.utcnow()),
            period_end=data.get("period_end", datetime.utcnow()),
            total_orchestrations=data.get("total_orchestrations", 0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            avg_duration_ms=data.get("avg_duration_ms"),
            p95_duration_ms=data.get("p95_duration_ms"),
            top_slow_stages=[{"stage": s, "duration_ms": d} for s, d in sorted_stages[:5]],
        ).model_dump()

    def _provider_report(self, data: dict[str, Any]) -> dict[str, Any]:
        total = data.get("total_requests", 0)
        failures = data.get("failure_count", 0)
        return ProviderReport(
            provider=data.get("provider", "unknown"),
            total_requests=total,
            success_count=data.get("success_count", 0),
            failure_count=failures,
            avg_latency_ms=data.get("avg_latency_ms"),
            error_rate=(failures / total * 100) if total > 0 else None,
        ).model_dump()

    def _usage_report(self, data: dict[str, Any]) -> dict[str, Any]:
        return UsageReport(
            total_ai_requests=data.get("total_ai_requests", 0),
            total_tokens=data.get("total_tokens", 0),
            estimated_cost=data.get("estimated_cost", 0.0),
            model_breakdown=data.get("model_breakdown", {}),
        ).model_dump()

    def _failure_report(self, data: dict[str, Any]) -> dict[str, Any]:
        return FailureReport(
            total_failures=data.get("total_failures", 0),
            failures_by_stage=data.get("failures_by_stage", {}),
            failures_by_error=data.get("failures_by_error", {}),
            top_failures=data.get("top_failures", []),
        ).model_dump()

    def _system_summary(self, data: dict[str, Any]) -> dict[str, Any]:
        total = data.get("total_orchestrations", 0)
        failures = data.get("total_failures", 0)
        return SystemSummary(
            uptime_hours=data.get("uptime_hours", 0.0),
            total_orchestrations=total,
            active_orchestrations=data.get("active_orchestrations", 0),
            total_ai_requests=data.get("total_ai_requests", 0),
            total_browser_actions=data.get("total_browser_actions", 0),
            total_uploads=data.get("total_uploads", 0),
            total_submissions=data.get("total_submissions", 0),
            error_rate=(failures / total * 100) if total > 0 else None,
        ).model_dump()
