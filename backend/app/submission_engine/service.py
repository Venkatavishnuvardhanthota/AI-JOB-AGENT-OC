from __future__ import annotations

from typing import Any

import structlog

from app.submission_engine.config import SubmissionEngineConfig
from app.submission_engine.factory import SubmissionProviderFactory
from app.submission_engine.orchestrator import SubmissionOrchestratorEngine
from app.submission_engine.registry import SubmissionProviderRegistry
from app.submission_engine.schemas import (
    ExecutionMode,
    SubmissionReport,
    SubmissionState,
    SubmissionStatus,
)
from app.submission_engine.state import SubmissionStateMachine
from app.submission_engine.validator import SubmissionValidatorEngine

logger = structlog.get_logger(__name__)


class SubmissionEngineService:
    def __init__(
        self,
        registry: SubmissionProviderRegistry,
        factory: SubmissionProviderFactory,
        config: SubmissionEngineConfig | None = None,
    ) -> None:
        self._registry = registry
        self._factory = factory
        self._config = config or SubmissionEngineConfig()
        self._logger = logger.bind(service="submission_engine")

        self._state_machine = SubmissionStateMachine()
        self._validator = SubmissionValidatorEngine(self._config)
        self._orchestrator = SubmissionOrchestratorEngine(
            validator=self._validator,
            state_machine=self._state_machine,
        )

    def create_submission_status(
        self,
        package_id: str,
        provider_name: str = "",
        execution_mode: ExecutionMode = ExecutionMode.DRY_RUN,
    ) -> SubmissionStatus:
        status = SubmissionStatus(
            package_id=package_id,
            provider_name=provider_name,
            execution_mode=execution_mode,
            state=SubmissionState.PENDING,
        )
        return status

    def validate_submission(
        self,
        page: Any,
        execution_plan: Any,
        upload_plan: Any | None = None,
        workflow_service: Any | None = None,
        review_service: Any | None = None,
        workflow_id: str | None = None,
        package_id: str | None = None,
    ) -> list[str]:
        issues = self._validator.validate(page, execution_plan, upload_plan)

        if workflow_service and workflow_id:
            issues.extend(self._validator.validate_workflow(workflow_service, workflow_id))

        if review_service and package_id:
            issues.extend(self._validator.validate_review(review_service, package_id))

        return issues

    def execute_submission(
        self,
        page: Any,
        execution_plan: Any,
        upload_plan: Any | None = None,
        upload_service: Any | None = None,
        mode: ExecutionMode = ExecutionMode.DRY_RUN,
        provider_name: str | None = None,
    ) -> SubmissionReport:
        provider = self._get_provider(provider_name)

        return self._orchestrator.run(
            page=page,
            execution_plan=execution_plan,
            upload_plan=upload_plan,
            upload_service=upload_service,
            mode=mode,
            provider=provider,
        )

    def execute_submit_only(
        self,
        page: Any,
        provider_name: str | None = None,
        execution_mode: ExecutionMode = ExecutionMode.AUTOMATIC,
    ) -> SubmissionReport:
        provider = self._get_provider(provider_name)

        from app.submission_engine.reporting import ReportGeneratorEngine

        reporting = ReportGeneratorEngine()

        report = reporting.create_report(
            provider_name=getattr(provider, "name", "unknown") if provider else "unknown",
            execution_mode=execution_mode,
        )

        if execution_mode == ExecutionMode.DRY_RUN:
            return reporting.finalize_report(report, "completed", warnings=["Dry run — submit skipped"])

        try:
            result = provider.submit(page, self._config.submit_timeout_ms)
            if not result:
                return reporting.finalize_report(report, "failed", errors=["Submit failed"])

            confirmation = provider.confirm(page, self._config.confirmation_timeout_ms)
            report.confirmation_result = confirmation
            report.confirmation_number = confirmation.confirmation_number
            report.application_id = confirmation.application_id
            report.confirmation_url = confirmation.confirmation_url

            status = "completed" if confirmation.confirmed else "failed"
            errors = []
            if not confirmation.confirmed:
                errors.append("Confirmation failed")
            if confirmation.duplicate_detected:
                errors.append("Duplicate submission detected")

            return reporting.finalize_report(report, status, errors=errors if errors else None)

        except Exception as e:
            return reporting.finalize_report(report, "failed", errors=[f"Submit failed: {e}"])

    def confirm_submission(
        self,
        page: Any,
        provider_name: str | None = None,
    ) -> Any:
        provider = self._get_provider(provider_name)
        return provider.confirm(page, self._config.confirmation_timeout_ms)

    def get_provider_for_url(self, url: str) -> Any:
        provider = self._factory.detect_provider(url)
        if provider is None:
            if self._registry.is_registered("default"):
                return self._registry.resolve("default")
            default = self._factory.create_provider("default")
            return default
        return provider

    def detect_provider(self, url: str) -> str | None:
        provider = self.get_provider_for_url(url)
        if provider is None:
            return None
        return getattr(provider, "name", "default")

    def _get_provider(self, provider_name: str | None) -> Any:
        if provider_name:
            return self._registry.resolve(provider_name)
        if self._registry.is_registered("default"):
            return self._registry.resolve("default")
        return self._factory.create_provider("default")
