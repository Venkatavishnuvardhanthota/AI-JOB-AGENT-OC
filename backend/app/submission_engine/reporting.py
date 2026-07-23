from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog

from app.submission_engine.interfaces import ReportGenerator
from app.submission_engine.schemas import StepExecution, SubmissionReport, SubmissionStatus

logger = structlog.get_logger(__name__)


class ReportGeneratorEngine(ReportGenerator):
    def __init__(self) -> None:
        self._logger = logger.bind(service="report_generator")

    def generate(self, status: SubmissionStatus) -> SubmissionReport:
        report = status.report.model_copy(deep=True)
        report.report_id = status.report.report_id
        report.provider_name = status.provider_name
        report.execution_mode = status.execution_mode
        report.status = status.state.value

        if report.started_at and report.completed_at:
            delta = (report.completed_at - report.started_at).total_seconds() * 1000
            report.duration_ms = round(delta, 2)

        report.warnings = list(status.warnings)
        report.errors = list(status.errors)

        return report

    def create_report(
        self,
        provider_name: str,
        execution_mode: Any,
        steps: list[StepExecution] | None = None,
    ) -> SubmissionReport:
        report = SubmissionReport(
            provider_name=provider_name,
            execution_mode=execution_mode,
            started_at=datetime.utcnow(),
        )
        if steps:
            report.steps = steps
        return report

    def finalize_report(
        self,
        report: SubmissionReport,
        status: str,
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
    ) -> SubmissionReport:
        report.completed_at = datetime.utcnow()
        report.status = status

        if report.started_at and report.completed_at:
            delta = (report.completed_at - report.started_at).total_seconds() * 1000
            report.duration_ms = round(delta, 2)

        if errors:
            report.errors.extend(errors)
        if warnings:
            report.warnings.extend(warnings)

        return report
