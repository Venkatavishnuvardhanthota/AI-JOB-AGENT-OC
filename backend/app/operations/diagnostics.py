from __future__ import annotations

from typing import Any

from app.operations.config import OperationsConfig
from app.operations.exceptions import DiagnosticsError
from app.operations.interfaces import DiagnosticsEngine
from app.operations.schemas import DiagnosticFinding


class OperationsDiagnosticsEngine(DiagnosticsEngine):
    def __init__(self, config: OperationsConfig) -> None:
        self._config = config

    def analyze(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        findings: list[DiagnosticFinding] = []

        try:
            findings.extend(self._check_slow_stages(context))
            findings.extend(self._check_high_retry(context))
            findings.extend(self._check_ai_failures(context))
            findings.extend(self._check_pipeline_bottlenecks(context))
            findings.extend(self._check_repeated_failures(context))
        except Exception as e:
            raise DiagnosticsError(f"Diagnostics analysis failed: {e}") from e

        return [f.model_dump() for f in findings]

    def _check_slow_stages(self, context: dict[str, Any]) -> list[DiagnosticFinding]:
        findings: list[DiagnosticFinding] = []
        stages = context.get("stages", {})
        threshold = self._config.slow_stage_threshold_ms
        for stage_name, stage_data in stages.items():
            if isinstance(stage_data, dict):
                duration = stage_data.get("duration_ms")
                if duration is not None and duration > threshold:
                    findings.append(
                        DiagnosticFinding(
                            severity="warning",
                            category="slow_stage",
                            message=f"Stage '{stage_name}' took {duration:.0f}ms (threshold: {threshold:.0f}ms)",
                            details={"stage": stage_name, "duration_ms": duration, "threshold_ms": threshold},
                        )
                    )
        return findings

    def _check_high_retry(self, context: dict[str, Any]) -> list[DiagnosticFinding]:
        findings: list[DiagnosticFinding] = []
        stages = context.get("stages", {})
        threshold = self._config.high_retry_threshold
        for stage_name, stage_data in stages.items():
            if isinstance(stage_data, dict):
                retry_count = stage_data.get("retry_count", 0)
                if retry_count >= threshold:
                    findings.append(
                        DiagnosticFinding(
                            severity="warning",
                            category="high_retry_rate",
                            message=f"Stage '{stage_name}' has {retry_count} retries (threshold: {threshold})",
                            details={"stage": stage_name, "retry_count": retry_count, "threshold": threshold},
                        )
                    )
        return findings

    def _check_ai_failures(self, context: dict[str, Any]) -> list[DiagnosticFinding]:
        findings: list[DiagnosticFinding] = []
        errors = context.get("errors", [])
        ai_errors = [e for e in errors if "ai" in e.lower() or "llm" in e.lower() or "provider" in e.lower()]
        if ai_errors:
            findings.append(
                DiagnosticFinding(
                    severity="error",
                    category="ai_failure",
                    message=f"{len(ai_errors)} AI-related error(s) detected",
                    details={"ai_errors": ai_errors, "count": len(ai_errors)},
                )
            )
        return findings

    def _check_pipeline_bottlenecks(self, context: dict[str, Any]) -> list[DiagnosticFinding]:
        findings: list[DiagnosticFinding] = []
        stages = context.get("stages", {})
        durations = []
        for stage_name, stage_data in stages.items():
            if isinstance(stage_data, dict):
                d = stage_data.get("duration_ms")
                if d is not None:
                    durations.append((stage_name, d))
        if len(durations) >= 2:
            durations.sort(key=lambda x: x[1], reverse=True)
            slowest = durations[0]
            second = durations[1] if len(durations) > 1 else None
            if second and slowest[1] > second[1] * 2:
                findings.append(
                    DiagnosticFinding(
                        severity="info",
                        category="pipeline_bottleneck",
                        message=(
                            f"Stage '{slowest[0]}' is a bottleneck" f" ({slowest[1]:.0f}ms, 2x next: {second[1]:.0f}ms)"
                        ),
                        details={
                            "stage": slowest[0],
                            "duration_ms": slowest[1],
                            "next_stage": second[0],
                            "next_duration_ms": second[1],
                        },
                    )
                )
        return findings

    def _check_repeated_failures(self, context: dict[str, Any]) -> list[DiagnosticFinding]:
        findings: list[DiagnosticFinding] = []
        errors = context.get("errors", [])
        if len(errors) >= 3:
            error_counts: dict[str, int] = {}
            for e in errors:
                error_counts[e] = error_counts.get(e, 0) + 1
            repeated = [(err, cnt) for err, cnt in error_counts.items() if cnt >= 2]
            for err, cnt in repeated:
                findings.append(
                    DiagnosticFinding(
                        severity="error",
                        category="repeated_failure",
                        message=f"Repeated failure ({cnt}x): {err}",
                        details={"error": err, "count": cnt},
                    )
                )
        return findings
