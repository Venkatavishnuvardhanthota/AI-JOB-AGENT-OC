from __future__ import annotations

import time
from datetime import datetime
from typing import Any

import structlog

from app.submission_engine.confirmation import SubmissionConfirmerEngine
from app.submission_engine.executor import FieldExecutorEngine
from app.submission_engine.metrics import MetricsTrackerEngine
from app.submission_engine.recovery import SubmissionRecoveryHandler
from app.submission_engine.reporting import ReportGeneratorEngine
from app.submission_engine.safety import SafetyGuardEngine
from app.submission_engine.schemas import (
    ConfirmationResult,
    ExecutionMode,
    StepExecution,
    SubmissionReport,
    SubmissionStepResult,
    SubmissionStepType,
)
from app.submission_engine.state import SubmissionStateMachine
from app.submission_engine.validator import SubmissionValidatorEngine

logger = structlog.get_logger(__name__)


class SubmissionOrchestratorEngine:
    def __init__(
        self,
        field_executor: FieldExecutorEngine | None = None,
        confirmer: SubmissionConfirmerEngine | None = None,
        recovery: SubmissionRecoveryHandler | None = None,
        safety: SafetyGuardEngine | None = None,
        metrics: MetricsTrackerEngine | None = None,
        reporting: ReportGeneratorEngine | None = None,
        state_machine: SubmissionStateMachine | None = None,
        validator: SubmissionValidatorEngine | None = None,
    ) -> None:
        self._field_executor = field_executor or FieldExecutorEngine()
        self._confirmer = confirmer or SubmissionConfirmerEngine()
        self._recovery = recovery or SubmissionRecoveryHandler()
        self._safety = safety or SafetyGuardEngine()
        self._metrics = metrics or MetricsTrackerEngine()
        self._reporting = reporting or ReportGeneratorEngine()
        self._state = state_machine or SubmissionStateMachine()
        self._validator = validator or SubmissionValidatorEngine()
        self._logger = logger.bind(service="submission_orchestrator")

    def run(
        self,
        page: Any,
        execution_plan: Any,
        upload_plan: Any | None = None,
        upload_service: Any | None = None,
        mode: ExecutionMode = ExecutionMode.DRY_RUN,
        provider: Any | None = None,
    ) -> SubmissionReport:
        if not isinstance(mode, ExecutionMode):
            try:
                mode = ExecutionMode(mode)
            except (ValueError, TypeError):
                report = SubmissionReport(
                    provider_name=getattr(provider, "name", "unknown") if provider else "unknown",
                    execution_mode=ExecutionMode.DRY_RUN,
                    started_at=datetime.utcnow(),
                )
                return self._reporting.finalize_report(report, "failed", errors=[f"Unknown execution mode: {mode}"])

        self._safety.set_mode(mode)
        self._metrics.reset()
        self._recovery.reset()

        if mode == ExecutionMode.DRY_RUN:
            return self._run_dry(page, execution_plan, upload_plan, provider)
        elif mode == ExecutionMode.MANUAL_CONFIRMATION:
            return self._run_with_confirmation(page, execution_plan, upload_plan, upload_service, provider)
        elif mode == ExecutionMode.AUTOMATIC:
            return self._run_automatic(page, execution_plan, upload_plan, upload_service, provider)
        elif mode == ExecutionMode.SAFE_RETRY:
            return self._run_safe_retry(page, execution_plan, upload_plan, upload_service, provider)
        else:
            report = self._reporting.create_report(
                provider_name=getattr(provider, "name", "unknown") if provider else "unknown",
                execution_mode=mode,
            )
            return self._reporting.finalize_report(report, "failed", errors=[f"Unknown execution mode: {mode}"])

    def _run_dry(
        self, page: Any, execution_plan: Any, upload_plan: Any | None, provider: Any | None
    ) -> SubmissionReport:
        report = self._reporting.create_report(
            provider_name=getattr(provider, "name", "unknown") if provider else "unknown",
            execution_mode=ExecutionMode.DRY_RUN,
        )
        start = time.time()

        steps = self._field_executor.execute_plan(page, execution_plan)
        report.steps = steps
        for step in steps:
            self._metrics.record_step(step)

        if upload_plan:
            tasks = getattr(upload_plan, "tasks", [])
            for task in tasks:
                self._metrics.record_step(StepExecution(
                    step_type=SubmissionStepType.UPLOAD,
                    field_ref=getattr(task, "field_ref", ""),
                    result=SubmissionStepResult.SKIPPED,
                ))

        report.metrics = self._metrics.get_metrics()
        report.metrics.total_duration_ms = round((time.time() - start) * 1000, 2)

        return self._reporting.finalize_report(
            report, "completed", warnings=["Dry run — no actual submission performed"]
        )

    def _run_with_confirmation(
        self, page: Any, execution_plan: Any, upload_plan: Any | None,
        upload_service: Any | None, provider: Any | None
    ) -> SubmissionReport:
        report = self._reporting.create_report(
            provider_name=getattr(provider, "name", "unknown") if provider else "unknown",
            execution_mode=ExecutionMode.MANUAL_CONFIRMATION,
        )
        start = time.time()

        safety_checks = self._safety.check(ExecutionMode.MANUAL_CONFIRMATION)
        report.safety_checks = safety_checks

        steps = self._field_executor.execute_plan(page, execution_plan)
        report.steps = steps
        for step in steps:
            self._metrics.record_step(step)

        if upload_service and upload_plan:
            try:
                upload_results = upload_service.execute_upload_plan(page, upload_plan)
                for r in upload_results:
                    self._metrics.record_step(StepExecution(
                        step_type=SubmissionStepType.UPLOAD,
                        field_ref=getattr(r, "field_ref", ""),
                        result=(
                            SubmissionStepResult.SUCCESS
                            if getattr(r, "result", None) and str(getattr(r, "result", "")) == "success"
                            else SubmissionStepResult.SKIPPED
                        ),
                    ))
                report.warnings.append("Uploads executed — manual confirmation required before submit")
            except Exception as e:
                report.errors.append(f"Upload execution failed: {e}")

        report.metrics = self._metrics.get_metrics()
        report.metrics.total_duration_ms = round((time.time() - start) * 1000, 2)
        report.manual_actions.append("Manual confirmation required before final submission")

        return self._reporting.finalize_report(report, "awaiting_confirmation")

    def _run_automatic(
        self, page: Any, execution_plan: Any, upload_plan: Any | None,
        upload_service: Any | None, provider: Any | None
    ) -> SubmissionReport:
        report = self._reporting.create_report(
            provider_name=getattr(provider, "name", "unknown") if provider else "unknown",
            execution_mode=ExecutionMode.AUTOMATIC,
        )
        start = time.time()

        safety_checks = self._safety.check(ExecutionMode.AUTOMATIC)
        report.safety_checks = safety_checks

        steps = self._field_executor.execute_plan(page, execution_plan)
        report.steps = steps
        for step in steps:
            self._metrics.record_step(step)

        if upload_service and upload_plan:
            try:
                upload_results = upload_service.execute_upload_plan(page, upload_plan)
                for r in upload_results:
                    self._metrics.record_step(StepExecution(
                        step_type=SubmissionStepType.UPLOAD,
                        field_ref=getattr(r, "field_ref", ""),
                        result=(
                            SubmissionStepResult.SUCCESS
                            if getattr(r, "result", None) and str(getattr(r, "result", "")) == "success"
                            else SubmissionStepResult.FAILED
                        ),
                    ))
            except Exception as e:
                report.errors.append(f"Upload execution failed: {e}")
                return self._reporting.finalize_report(report, "failed", errors=[f"Upload execution failed: {e}"])

        submit_result = self._execute_submit(page, provider, report)
        if not submit_result:
            return self._reporting.finalize_report(report, "failed", errors=["Submit failed"])

        confirm_start = time.time()
        confirmation = self._verify_submission(page, provider)
        if confirmation.duration_ms is None:
            confirmation.duration_ms = round((time.time() - confirm_start) * 1000, 2)
        report.confirmation_result = confirmation

        if confirmation.confirmed:
            report.confirmation_number = confirmation.confirmation_number
            report.application_id = confirmation.application_id
            report.confirmation_url = confirmation.confirmation_url

        report.metrics = self._metrics.get_metrics()
        report.metrics.total_duration_ms = round((time.time() - start) * 1000, 2)

        status = "completed" if confirmation.confirmed else "failed"
        errors = []
        if not confirmation.confirmed:
            errors.append("Submission confirmation failed")
        if confirmation.duplicate_detected:
            errors.append("Duplicate submission detected")

        return self._reporting.finalize_report(report, status, errors=errors if errors else None)

    def _run_safe_retry(
        self, page: Any, execution_plan: Any, upload_plan: Any | None,
        upload_service: Any | None, provider: Any | None
    ) -> SubmissionReport:
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                if attempt > 1:
                    self._recovery.record_attempt(f"Attempt {attempt}", duration_ms=0.0)
                return self._run_automatic(page, execution_plan, upload_plan, upload_service, provider)
            except Exception as e:
                error_msg = str(e)
                self._metrics.increment_retry()
                self._recovery.record_attempt(error_msg)

                if not self._recovery.can_retry(error_msg, attempt):
                    report = self._reporting.create_report(
                        provider_name=getattr(provider, "name", "unknown") if provider else "unknown",
                        execution_mode=ExecutionMode.SAFE_RETRY,
                    )
                    report.retry_attempts = self._recovery.get_attempts()
                    return self._reporting.finalize_report(
                        report, "failed", errors=[f"Non-retryable error: {error_msg}"]
                    )

                if attempt < max_attempts:
                    self._recovery.recover(page, error_msg, attempt)
                    continue

        report = self._reporting.create_report(
            provider_name=getattr(provider, "name", "unknown") if provider else "unknown",
            execution_mode=ExecutionMode.SAFE_RETRY,
        )
        report.retry_attempts = self._recovery.get_attempts()
        return self._reporting.finalize_report(report, "failed", errors=["Max retry attempts exceeded"])

    def _execute_submit(self, page: Any, provider: Any, report: SubmissionReport) -> bool:
        if provider is None:
            report.errors.append("No provider available for submission")
            return False

        timeout_ms = 60000.0
        try:
            result = provider.submit(page, timeout_ms)
            if result:
                self._metrics.increment_screenshots()
                return True
            report.errors.append("Submit returned False")
            return False
        except Exception as e:
            report.errors.append(f"Submit failed: {e}")
            return False

    def _verify_submission(self, page: Any, provider: Any) -> ConfirmationResult:
        if provider is None:
            return ConfirmationResult(details="No provider available for confirmation")

        try:
            return provider.confirm(page, 15000.0)
        except Exception as e:
            return ConfirmationResult(details=f"Confirmation check failed: {e}")
