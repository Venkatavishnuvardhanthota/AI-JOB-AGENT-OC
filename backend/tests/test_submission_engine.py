from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.submission_engine.config import SubmissionEngineConfig
from app.submission_engine.confirmation import SubmissionConfirmerEngine
from app.submission_engine.dependencies import (
    get_submission_config,
    get_submission_engine_service,
    get_submission_factory,
    get_submission_registry,
    reset_submission_engine_service,
)
from app.submission_engine.exceptions import (
    SubmissionConfigError,
    SubmissionConfirmationError,
    SubmissionEngineError,
    SubmissionExecutionError,
    SubmissionProviderNotFoundError,
    SubmissionRecoveryError,
    SubmissionRejectedError,
    SubmissionSafetyError,
    SubmissionTimeoutError,
    SubmissionValidationError,
)
from app.submission_engine.executor import FieldExecutorEngine
from app.submission_engine.factory import SubmissionProviderFactory
from app.submission_engine.metrics import MetricsTrackerEngine
from app.submission_engine.orchestrator import SubmissionOrchestratorEngine
from app.submission_engine.providers.base import BaseSubmissionProvider
from app.submission_engine.recovery import SubmissionRecoveryHandler
from app.submission_engine.registry import SubmissionProviderRegistry
from app.submission_engine.reporting import ReportGeneratorEngine
from app.submission_engine.safety import SafetyGuardEngine
from app.submission_engine.schemas import (
    ConfirmationResult,
    ExecutionMetrics,
    ExecutionMode,
    RetryAttempt,
    SafetyCheck,
    StepExecution,
    SubmissionReport,
    SubmissionState,
    SubmissionStatus,
    SubmissionStepResult,
    SubmissionStepType,
)
from app.submission_engine.service import SubmissionEngineService
from app.submission_engine.state import SubmissionStateMachine
from app.submission_engine.validator import SubmissionValidatorEngine

# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def config() -> SubmissionEngineConfig:
    return SubmissionEngineConfig()


@pytest.fixture
def registry() -> SubmissionProviderRegistry:
    return SubmissionProviderRegistry()


@pytest.fixture
def factory(registry) -> SubmissionProviderFactory:
    return SubmissionProviderFactory(registry=registry)


@pytest.fixture
def service(registry, factory, config) -> SubmissionEngineService:
    return SubmissionEngineService(registry=registry, factory=factory, config=config)


@pytest.fixture
def mock_page() -> MagicMock:
    page = MagicMock()
    element = MagicMock()
    element.is_visible.return_value = True
    element.is_checked.return_value = False
    element.fill.return_value = None
    page.locator.return_value = element
    page.url = "https://example.com/apply"
    page.text_content.return_value = "Thank you for your application"
    return page


@pytest.fixture
def mock_execution_plan() -> MagicMock:
    plan = MagicMock()
    plan.steps = []
    return plan


@pytest.fixture
def mock_step() -> MagicMock:
    step = MagicMock()
    step.step_type = type("StepType", (), {"value": "fill"})()
    step.field_ref = "first_name"
    step.selector = "#first_name"
    step.value = "John"
    step.source_path = None
    return step


@pytest.fixture
def mock_upload_plan() -> MagicMock:
    plan = MagicMock()
    task = MagicMock()
    task.field_ref = "resume"
    task.selector = "#resume-input"
    task.source = MagicMock()
    task.source.path = "/path/resume.pdf"
    plan.tasks = [task]
    return plan


@pytest.fixture
def mock_provider() -> MagicMock:
    provider = MagicMock()
    provider.name = "test_provider"
    provider.supports.return_value = True
    provider.submit.return_value = True
    provider.confirm.return_value = ConfirmationResult(
        confirmed=True,
        confirmation_number="CONF-123",
        application_id="APP-456",
        success_page_detected=True,
        provider_acknowledged=True,
    )
    return provider


@pytest.fixture
def state_machine() -> SubmissionStateMachine:
    return SubmissionStateMachine()


@pytest.fixture
def validator() -> SubmissionValidatorEngine:
    return SubmissionValidatorEngine()


@pytest.fixture
def executor() -> FieldExecutorEngine:
    return FieldExecutorEngine()


@pytest.fixture
def confirmer() -> SubmissionConfirmerEngine:
    return SubmissionConfirmerEngine()


@pytest.fixture
def recovery() -> SubmissionRecoveryHandler:
    return SubmissionRecoveryHandler()


@pytest.fixture
def safety() -> SafetyGuardEngine:
    return SafetyGuardEngine()


@pytest.fixture
def metrics_tracker() -> MetricsTrackerEngine:
    return MetricsTrackerEngine()


@pytest.fixture
def report_gen() -> ReportGeneratorEngine:
    return ReportGeneratorEngine()


# ─── Test Exceptions ─────────────────────────────────────────────────────────


class TestExceptions:
    def test_submission_engine_error(self):
        err = SubmissionEngineError("test")
        assert err.code == "SUBMISSION_ENGINE_ERROR"

    def test_validation_error(self):
        err = SubmissionValidationError("invalid")
        assert err.code == "SUBMISSION_VALIDATION_ERROR"
        assert err.status_code == 400

    def test_execution_error(self):
        err = SubmissionExecutionError("failed")
        assert err.code == "SUBMISSION_EXECUTION_ERROR"

    def test_confirmation_error(self):
        err = SubmissionConfirmationError("confirm failed")
        assert err.code == "SUBMISSION_CONFIRMATION_ERROR"

    def test_recovery_error(self):
        err = SubmissionRecoveryError("recovery failed")
        assert err.code == "SUBMISSION_RECOVERY_ERROR"

    def test_safety_error(self):
        err = SubmissionSafetyError("blocked")
        assert err.code == "SUBMISSION_SAFETY_ERROR"
        assert err.status_code == 400

    def test_timeout_error(self):
        err = SubmissionTimeoutError("timed out")
        assert err.code == "SUBMISSION_TIMEOUT_ERROR"

    def test_rejected_error(self):
        err = SubmissionRejectedError("rejected")
        assert err.code == "SUBMISSION_REJECTED_ERROR"

    def test_provider_not_found(self):
        err = SubmissionProviderNotFoundError("not found")
        assert err.code == "SUBMISSION_PROVIDER_NOT_FOUND"
        assert err.status_code == 404

    def test_config_error(self):
        err = SubmissionConfigError("bad config")
        assert err.code == "SUBMISSION_CONFIG_ERROR"


# ─── Test Config ─────────────────────────────────────────────────────────────


class TestConfig:
    def test_defaults(self):
        cfg = SubmissionEngineConfig()
        assert cfg.execution_mode == "dry_run"
        assert cfg.require_review_approval is True
        assert cfg.max_retry_attempts == 3
        assert cfg.step_timeout_ms == 30000.0
        assert cfg.submit_timeout_ms == 60000.0
        assert "dry_run" in cfg.valid_execution_modes

    def test_valid_modes(self):
        cfg = SubmissionEngineConfig()
        assert "dry_run" in cfg.valid_execution_modes
        assert "manual_confirmation" in cfg.valid_execution_modes
        assert "automatic" in cfg.valid_execution_modes
        assert "safe_retry" in cfg.valid_execution_modes


# ─── Test Schemas ────────────────────────────────────────────────────────────


class TestSchemas:
    def test_execution_mode_enum(self):
        assert ExecutionMode.DRY_RUN.value == "dry_run"
        assert ExecutionMode.AUTOMATIC.value == "automatic"

    def test_submission_step_type_enum(self):
        assert SubmissionStepType.FILL.value == "fill"
        assert SubmissionStepType.SUBMIT.value == "submit"
        assert SubmissionStepType.CONFIRM.value == "confirm"

    def test_submission_step_result_enum(self):
        assert SubmissionStepResult.PENDING.value == "pending"
        assert SubmissionStepResult.SUCCESS.value == "success"

    def test_step_execution_defaults(self):
        se = StepExecution(step_type=SubmissionStepType.FILL, field_ref="f1")
        assert se.result == SubmissionStepResult.PENDING

    def test_confirmation_result_defaults(self):
        cr = ConfirmationResult()
        assert cr.confirmed is False

    def test_execution_metrics_defaults(self):
        em = ExecutionMetrics()
        assert em.total_fields == 0

    def test_retry_attempt_defaults(self):
        ra = RetryAttempt(attempt_number=1, error="test error")
        assert ra.error == "test error"

    def test_safety_check_defaults(self):
        sc = SafetyCheck()
        assert sc.passed is False

    def test_submission_report_defaults(self):
        sr = SubmissionReport()
        assert sr.status == "pending"
        assert sr.errors == []

    def test_submission_state_enum(self):
        assert SubmissionState.PENDING.value == "pending"
        assert SubmissionState.COMPLETED.value == "completed"

    def test_submission_status_defaults(self):
        ss = SubmissionStatus(package_id="pkg-1")
        assert ss.state == SubmissionState.PENDING
        assert ss.errors == []

    def test_report_generates_uuid(self):
        r1 = SubmissionReport()
        r2 = SubmissionReport()
        assert r1.report_id != r2.report_id


# ─── Test State Machine ──────────────────────────────────────────────────────


class TestStateMachine:
    def test_can_transition_valid(self, state_machine):
        assert state_machine.can_transition(SubmissionState.PENDING, SubmissionState.VALIDATING)

    def test_can_transition_invalid(self, state_machine):
        assert not state_machine.can_transition(SubmissionState.PENDING, SubmissionState.COMPLETED)

    def test_transition(self, state_machine):
        status = SubmissionStatus(package_id="pkg-1")
        result = state_machine.transition(status, SubmissionState.VALIDATING)
        assert result.state == SubmissionState.VALIDATING

    def test_transition_invalid_raises(self, state_machine):
        status = SubmissionStatus(package_id="pkg-1")
        with pytest.raises(ValueError):
            state_machine.transition(status, SubmissionState.COMPLETED)

    def test_get_allowed_transitions_pending(self, state_machine):
        allowed = state_machine.get_allowed_transitions(SubmissionState.PENDING)
        assert SubmissionState.VALIDATING in allowed
        assert SubmissionState.CANCELLED in allowed

    def test_is_terminal_completed(self, state_machine):
        assert state_machine.is_terminal(SubmissionState.COMPLETED)

    def test_is_terminal_cancelled(self, state_machine):
        assert state_machine.is_terminal(SubmissionState.CANCELLED)

    def test_is_terminal_pending(self, state_machine):
        assert not state_machine.is_terminal(SubmissionState.PENDING)

    def test_is_failure_failed(self, state_machine):
        assert state_machine.is_failure(SubmissionState.FAILED)

    def test_is_failure_blocked(self, state_machine):
        assert state_machine.is_failure(SubmissionState.BLOCKED)

    def test_is_failure_pending(self, state_machine):
        assert not state_machine.is_failure(SubmissionState.PENDING)

    def test_full_flow(self, state_machine):
        status = SubmissionStatus(package_id="pkg-1")
        transitions = [
            SubmissionState.VALIDATING,
            SubmissionState.VALIDATED,
            SubmissionState.EXECUTING_FIELDS,
            SubmissionState.EXECUTING_UPLOADS,
            SubmissionState.AWAITING_CONFIRMATION,
            SubmissionState.SUBMITTING,
            SubmissionState.CONFIRMING,
            SubmissionState.COMPLETED,
        ]
        for target in transitions:
            status = state_machine.transition(status, target)
        assert status.state == SubmissionState.COMPLETED


# ─── Test Executor ───────────────────────────────────────────────────────────


class TestFieldExecutor:
    def test_execute_fill(self, executor, mock_page, mock_step):
        result = executor.execute_step(mock_page, mock_step)
        assert result.step_type == SubmissionStepType.FILL
        assert result.result == SubmissionStepResult.SUCCESS

    def test_execute_skip(self, executor, mock_page):
        step = MagicMock()
        step.step_type = type("StepType", (), {"value": "skip"})()
        step.field_ref = "f1"
        step.selector = "#f1"
        result = executor.execute_step(mock_page, step)
        assert result.result == SubmissionStepResult.SKIPPED

    def test_execute_manual(self, executor, mock_page):
        step = MagicMock()
        step.step_type = type("StepType", (), {"value": "request_manual"})()
        step.field_ref = "f1"
        step.selector = "#f1"
        result = executor.execute_step(mock_page, step)
        assert result.result == SubmissionStepResult.SKIPPED

    def test_execute_select(self, executor, mock_page):
        step = MagicMock()
        step.step_type = type("StepType", (), {"value": "select"})()
        step.field_ref = "f1"
        step.selector = "#f1"
        step.value = "option1"
        result = executor.execute_step(mock_page, step)
        assert result.result == SubmissionStepResult.SUCCESS

    def test_execute_check(self, executor, mock_page):
        step = MagicMock()
        step.step_type = type("StepType", (), {"value": "check"})()
        step.field_ref = "f1"
        step.selector = "#f1"
        step.value = True
        result = executor.execute_step(mock_page, step)
        assert result.result == SubmissionStepResult.SUCCESS

    def test_execute_upload_skipped(self, executor, mock_page):
        step = MagicMock()
        step.step_type = type("StepType", (), {"value": "upload"})()
        step.field_ref = "f1"
        step.selector = ""
        result = executor.execute_step(mock_page, step)
        assert result.result == SubmissionStepResult.SKIPPED

    def test_execute_fill_element_not_visible(self, executor, mock_page):
        element = mock_page.locator.return_value
        element.is_visible.return_value = False
        step = MagicMock()
        step.step_type = type("StepType", (), {"value": "fill"})()
        step.field_ref = "f1"
        step.selector = "#f1"
        step.value = "test"
        result = executor.execute_step(mock_page, step)
        assert result.result == SubmissionStepResult.FAILED

    def test_execute_plan_empty(self, executor, mock_page):
        plan = MagicMock()
        plan.steps = []
        results = executor.execute_plan(mock_page, plan)
        assert len(results) == 0

    def test_execute_plan_with_steps(self, executor, mock_page):
        step = MagicMock()
        step.step_type = type("StepType", (), {"value": "fill"})()
        step.field_ref = "f1"
        step.selector = "#f1"
        step.value = "test"
        plan = MagicMock()
        plan.steps = [step, step]
        results = executor.execute_plan(mock_page, plan)
        assert len(results) == 2

    def test_execute_select_not_visible(self, executor, mock_page):
        element = mock_page.locator.return_value
        element.is_visible.return_value = False
        step = MagicMock()
        step.step_type = type("StepType", (), {"value": "select"})()
        step.field_ref = "f1"
        step.selector = "#f1"
        step.value = "opt1"
        result = executor.execute_step(mock_page, step)
        assert result.result == SubmissionStepResult.FAILED

    def test_execute_fill_no_page(self, executor):
        step = MagicMock()
        step.step_type = type("StepType", (), {"value": "fill"})()
        step.field_ref = "f1"
        step.selector = "#f1"
        step.value = "test"
        result = executor.execute_step(None, step)
        assert result.result == SubmissionStepResult.FAILED


# ─── Test Confirmation ───────────────────────────────────────────────────────


class TestConfirmation:
    def test_confirm_no_page(self, confirmer):
        result = confirmer.confirm(None, 1000)
        assert result.confirmed is False
        assert "page is not available" in result.details.lower()

    def test_confirm_success(self, confirmer, mock_page):
        result = confirmer.confirm(mock_page, 5000)
        assert result.success_page_detected is True
        assert result.provider_acknowledged is True

    def test_confirm_duplicate(self, confirmer, mock_page):
        mock_page.text_content.return_value = "You have already applied for this position"
        result = confirmer.confirm(mock_page, 5000)
        assert result.duplicate_detected is True

    def test_confirm_redirect(self, confirmer):
        page = MagicMock()
        page.url = "https://example.com/application/confirmation"
        page.text_content.return_value = "some content"
        result = confirmer.confirm(page, 5000)
        assert result.redirect_url == "https://example.com/application/confirmation"

    def test_confirm_extracts_id(self, confirmer, mock_page):
        mock_page.text_content.return_value = "Application ID: APP-12345 has been submitted"
        result = confirmer.confirm(mock_page, 5000)
        assert result.success_page_detected is True


# ─── Test Recovery ───────────────────────────────────────────────────────────


class TestRecovery:
    def test_can_retry_default(self, recovery):
        assert recovery.can_retry("timeout error", 1)

    def test_can_retry_exhausted(self, recovery):
        assert not recovery.can_retry("timeout", 3)

    def test_can_retry_non_retryable(self, recovery):
        assert not recovery.can_retry("validation failed", 1)

    def test_record_attempt(self, recovery):
        attempt = recovery.record_attempt("error occurred", 100.0)
        assert attempt.attempt_number == 1
        assert attempt.error == "error occurred"

    def test_get_attempts(self, recovery):
        recovery.record_attempt("error 1")
        recovery.record_attempt("error 2")
        attempts = recovery.get_attempts()
        assert len(attempts) == 2

    def test_reset(self, recovery):
        recovery.record_attempt("error")
        recovery.reset()
        assert len(recovery.get_attempts()) == 0

    def test_recover(self, recovery, mock_page):
        result = recovery.recover(mock_page, "timeout", 1)
        assert result is True

    def test_recover_non_retryable_raises(self, recovery):
        with pytest.raises(SubmissionRecoveryError):
            recovery.recover(None, "validation failed", 10)

    def test_compute_delay(self, recovery):
        delay = recovery._compute_delay(1)
        assert delay == recovery._config.retry_delay_seconds


# ─── Test Safety ─────────────────────────────────────────────────────────────


class TestSafety:
    def test_allow_submit_dry_run(self, safety):
        safety.set_mode(ExecutionMode.DRY_RUN)
        assert not safety.allow_submit()

    def test_allow_submit_automatic(self, safety):
        safety.set_mode(ExecutionMode.AUTOMATIC)
        assert safety.allow_submit()

    def test_allow_submit_manual(self, safety):
        safety.set_mode(ExecutionMode.MANUAL_CONFIRMATION)
        assert safety.allow_submit()

    def test_is_dry_run(self, safety):
        safety.set_mode(ExecutionMode.DRY_RUN)
        assert safety.is_dry_run()

    def test_is_not_dry_run(self, safety):
        safety.set_mode(ExecutionMode.AUTOMATIC)
        assert not safety.is_dry_run()

    def test_require_manual_confirmation(self, safety):
        safety.set_mode(ExecutionMode.MANUAL_CONFIRMATION)
        assert safety.require_manual_confirmation()

    def test_assert_can_submit_dry_run_raises(self, safety):
        safety.set_mode(ExecutionMode.DRY_RUN)
        with pytest.raises(SubmissionSafetyError):
            safety.assert_can_submit()

    def test_assert_can_submit_automatic(self, safety):
        safety.set_mode(ExecutionMode.AUTOMATIC)
        safety.assert_can_submit()

    def test_check_execution_mode(self, safety):
        checks = safety.check(ExecutionMode.DRY_RUN)
        assert len(checks) > 0

    def test_get_checks(self, safety):
        safety.check(ExecutionMode.DRY_RUN)
        assert len(safety.get_checks()) > 0


# ─── Test Metrics ────────────────────────────────────────────────────────────


class TestMetrics:
    def test_record_step_fill(self, metrics_tracker):
        step = StepExecution(step_type=SubmissionStepType.FILL, field_ref="f1", result=SubmissionStepResult.SUCCESS)
        metrics_tracker.record_step(step)
        metrics = metrics_tracker.get_metrics()
        assert metrics.total_fields == 1
        assert metrics.filled_fields == 1
        assert metrics.success_count == 1

    def test_record_step_failed(self, metrics_tracker):
        step = StepExecution(step_type=SubmissionStepType.FILL, field_ref="f1", result=SubmissionStepResult.FAILED)
        metrics_tracker.record_step(step)
        metrics = metrics_tracker.get_metrics()
        assert metrics.failure_count == 1

    def test_record_step_upload(self, metrics_tracker):
        step = StepExecution(step_type=SubmissionStepType.UPLOAD, field_ref="f1", result=SubmissionStepResult.SUCCESS)
        metrics_tracker.record_step(step)
        metrics = metrics_tracker.get_metrics()
        assert metrics.upload_count == 1

    def test_set_durations(self, metrics_tracker):
        metrics_tracker.set_upload_duration(100.0)
        metrics_tracker.set_submit_duration(200.0)
        metrics_tracker.set_confirmation_duration(50.0)
        metrics_tracker.set_total_duration(500.0)
        metrics = metrics_tracker.get_metrics()
        assert metrics.upload_duration_ms == 100.0
        assert metrics.submit_duration_ms == 200.0
        assert metrics.total_duration_ms == 500.0

    def test_increment_retry(self, metrics_tracker):
        metrics_tracker.increment_retry()
        metrics = metrics_tracker.get_metrics()
        assert metrics.retry_count == 1

    def test_increment_screenshots(self, metrics_tracker):
        metrics_tracker.increment_screenshots(3)
        metrics = metrics_tracker.get_metrics()
        assert metrics.screenshots_taken == 3

    def test_reset(self, metrics_tracker):
        step = StepExecution(step_type=SubmissionStepType.FILL, field_ref="f1", result=SubmissionStepResult.SUCCESS)
        metrics_tracker.record_step(step)
        metrics_tracker.reset()
        metrics = metrics_tracker.get_metrics()
        assert metrics.total_fields == 0


# ─── Test Reporting ──────────────────────────────────────────────────────────


class TestReporting:
    def test_create_report(self, report_gen):
        report = report_gen.create_report("test_provider", ExecutionMode.DRY_RUN)
        assert report.provider_name == "test_provider"
        assert report.execution_mode == ExecutionMode.DRY_RUN
        assert report.started_at is not None

    def test_finalize_report(self, report_gen):
        report = report_gen.create_report("test", ExecutionMode.AUTOMATIC)
        result = report_gen.finalize_report(report, "completed")
        assert result.status == "completed"
        assert result.completed_at is not None

    def test_finalize_with_errors(self, report_gen):
        report = report_gen.create_report("test", ExecutionMode.AUTOMATIC)
        result = report_gen.finalize_report(report, "failed", errors=["error 1"])
        assert "error 1" in result.errors

    def test_generate_from_status(self, report_gen):
        status = SubmissionStatus(package_id="pkg-1", provider_name="test")
        report = report_gen.generate(status)
        assert report.provider_name == "test"

    def test_create_report_with_steps(self, report_gen):
        steps = [StepExecution(step_type=SubmissionStepType.FILL, field_ref="f1")]
        report = report_gen.create_report("test", ExecutionMode.DRY_RUN, steps=steps)
        assert len(report.steps) == 1


# ─── Test Validator ──────────────────────────────────────────────────────────


class TestValidator:
    def test_validate_no_page(self, validator):
        issues = validator.validate(None, None)
        assert any("page is not available" in i.lower() for i in issues)

    def test_validate_no_plan(self, validator, mock_page):
        issues = validator.validate(mock_page, None)
        assert any("execution plan" in i.lower() for i in issues)

    def test_validate_empty_plan(self, validator, mock_page):
        plan = MagicMock()
        plan.steps = []
        issues = validator.validate(mock_page, plan)
        assert any("no steps" in i.lower() for i in issues)

    def test_validate_valid(self, validator, mock_page):
        plan = MagicMock()
        plan.steps = [MagicMock()]
        issues = validator.validate(mock_page, plan)
        assert len(issues) == 0

    def test_validate_pre_submit_wrong_state(self, validator):
        status = SubmissionStatus(package_id="pkg-1", state=SubmissionState.PENDING)
        issues = validator.validate_pre_submit(status, None)
        assert any("state" in i.lower() for i in issues)

    def test_validate_workflow_not_ready(self, validator):
        wf = MagicMock()
        wf.get_status.return_value = MagicMock()
        wf.get_status.return_value.current_state = type("State", (), {"value": "discovered"})()
        issues = validator.validate_workflow(wf, "wf-1")
        assert len(issues) > 0

    def test_validate_review_not_approved(self, validator):
        rv = MagicMock()
        rv.get_review.return_value = MagicMock()
        rv.get_review.return_value.state = type("State", (), {"value": "pending"})()
        issues = validator.validate_review(rv, "pkg-1")
        assert len(issues) > 0

    def test_validate_review_no_record(self, validator):
        rv = MagicMock()
        rv.get_review.return_value = None
        issues = validator.validate_review(rv, "pkg-1")
        assert any("no review" in i.lower() for i in issues)


# ─── Test Provider ───────────────────────────────────────────────────────────


class TestBaseProvider:
    def test_supports(self):
        provider = BaseSubmissionProvider("test")
        assert provider.supports("https://example.com") is True

    def test_name(self):
        provider = BaseSubmissionProvider("my-provider")
        assert provider.name == "my-provider"

    def test_submit_no_page(self):
        provider = BaseSubmissionProvider("test")
        assert provider.submit(None, 1000) is False

    def test_confirm_no_page(self):
        provider = BaseSubmissionProvider("test")
        result = provider.confirm(None, 1000)
        assert result.confirmed is False


# ─── Test Registry ───────────────────────────────────────────────────────────


class TestRegistry:
    def test_register_and_resolve(self, registry):
        provider = BaseSubmissionProvider("test")
        registry.register("test", provider)
        assert registry.is_registered("test")
        assert registry.resolve("test") == provider

    def test_resolve_not_found(self, registry):
        with pytest.raises(SubmissionProviderNotFoundError):
            registry.resolve("nonexistent")

    def test_unregister(self, registry):
        registry.register("p1", BaseSubmissionProvider("p1"))
        registry.unregister("p1")
        assert not registry.is_registered("p1")

    def test_count(self, registry):
        assert registry.count() == 0
        registry.register("p1", BaseSubmissionProvider("p1"))
        assert registry.count() == 1

    def test_list(self, registry):
        registry.register("a", BaseSubmissionProvider("a"))
        registry.register("b", BaseSubmissionProvider("b"))
        assert "a" in registry.list_providers()

    def test_clear(self, registry):
        registry.register("p1", BaseSubmissionProvider("p1"))
        registry.clear()
        assert registry.count() == 0


# ─── Test Factory ────────────────────────────────────────────────────────────


class TestFactory:
    def test_create_provider(self, registry):
        factory = SubmissionProviderFactory(registry=registry)
        factory.create_provider("custom")
        assert registry.is_registered("custom")

    def test_register_all(self, registry):
        factory = SubmissionProviderFactory(registry=registry)
        factory.register_all()
        assert registry.is_registered("greenhouse")
        assert registry.is_registered("lever")
        assert registry.count() == 7

    def test_register_all_skips_existing(self, registry):
        factory = SubmissionProviderFactory(registry=registry)
        registry.register("greenhouse", BaseSubmissionProvider("greenhouse"))
        factory.register_all()
        assert registry.count() == 7

    def test_detect_provider(self, registry):
        factory = SubmissionProviderFactory(registry=registry)
        provider = BaseSubmissionProvider("test")
        registry.register("test", provider)
        detected = factory.detect_provider("https://example.com")
        assert detected == provider


# ─── Test Service ────────────────────────────────────────────────────────────


class TestService:
    def test_create_submission_status(self, service):
        status = service.create_submission_status("pkg-1", "test_provider")
        assert status.package_id == "pkg-1"
        assert status.provider_name == "test_provider"
        assert status.state == SubmissionState.PENDING

    def test_validate_submission(self, service, mock_page):
        plan = MagicMock()
        plan.steps = [MagicMock()]
        issues = service.validate_submission(mock_page, plan)
        assert len(issues) == 0

    def test_execute_submission_dry_run(self, service, mock_page, mock_execution_plan):
        report = service.execute_submission(
            page=mock_page,
            execution_plan=mock_execution_plan,
            mode=ExecutionMode.DRY_RUN,
        )
        assert report.execution_mode == ExecutionMode.DRY_RUN
        assert report.status == "completed"

    def test_execute_submit_only_dry(self, service, mock_page):
        report = service.execute_submit_only(mock_page, execution_mode=ExecutionMode.DRY_RUN)
        assert report.status == "completed"

    def test_get_provider_for_url_default(self, service, registry):
        provider = service.get_provider_for_url("https://example.com")
        assert provider is not None

    def test_detect_provider(self, service, registry):
        registry.register("default", BaseSubmissionProvider("default"))
        name = service.detect_provider("https://example.com")
        assert name == "default"


# ─── Test Dependencies ───────────────────────────────────────────────────────


class TestDependencies:
    def test_get_config(self):
        cfg = get_submission_config()
        assert isinstance(cfg, SubmissionEngineConfig)
        reset_submission_engine_service()

    def test_get_registry(self):
        reg = get_submission_registry()
        assert isinstance(reg, SubmissionProviderRegistry)
        reset_submission_engine_service()

    def test_get_registry_singleton(self):
        r1 = get_submission_registry()
        r2 = get_submission_registry()
        assert r1 is r2
        reset_submission_engine_service()

    def test_get_factory(self):
        factory = get_submission_factory()
        assert isinstance(factory, SubmissionProviderFactory)
        reset_submission_engine_service()

    def test_get_service(self):
        svc = get_submission_engine_service()
        assert isinstance(svc, SubmissionEngineService)
        reset_submission_engine_service()

    def test_get_service_singleton(self):
        s1 = get_submission_engine_service()
        s2 = get_submission_engine_service()
        assert s1 is s2
        reset_submission_engine_service()

    def test_reset(self):
        s1 = get_submission_engine_service()
        reset_submission_engine_service()
        s2 = get_submission_engine_service()
        assert s1 is not s2
        reset_submission_engine_service()

    def test_service_initializes_providers(self):
        svc = get_submission_engine_service()
        assert svc._registry.count() > 0
        reset_submission_engine_service()


# ─── Test Orchestrator ───────────────────────────────────────────────────────


class TestOrchestrator:
    def test_dry_run(self, mock_page, mock_execution_plan):
        orch = SubmissionOrchestratorEngine()
        report = orch.run(mock_page, mock_execution_plan, mode=ExecutionMode.DRY_RUN)
        assert report.status == "completed"

    def test_automatic(self, mock_page, mock_execution_plan, mock_provider):
        orch = SubmissionOrchestratorEngine()
        report = orch.run(mock_page, mock_execution_plan, mode=ExecutionMode.AUTOMATIC, provider=mock_provider)
        assert report.status == "completed"

    def test_manual_confirmation(self, mock_page, mock_execution_plan):
        orch = SubmissionOrchestratorEngine()
        report = orch.run(mock_page, mock_execution_plan, mode=ExecutionMode.MANUAL_CONFIRMATION)
        assert report.status == "awaiting_confirmation"

    def test_safe_retry(self, mock_page, mock_execution_plan, mock_provider):
        orch = SubmissionOrchestratorEngine()
        report = orch.run(mock_page, mock_execution_plan, mode=ExecutionMode.SAFE_RETRY, provider=mock_provider)
        assert report.status == "completed"

    def test_unknown_mode(self, mock_page, mock_execution_plan):
        orch = SubmissionOrchestratorEngine()
        report = orch.run(mock_page, mock_execution_plan, mode="unknown_mode")
        assert report.status == "failed"

    def test_dry_run_with_uploads(self, mock_page, mock_execution_plan, mock_upload_plan):
        orch = SubmissionOrchestratorEngine()
        report = orch.run(mock_page, mock_execution_plan, upload_plan=mock_upload_plan, mode=ExecutionMode.DRY_RUN)
        assert report.status == "completed"
        assert "dry run" in " ".join(report.warnings).lower()


# ─── Test Edge Cases ─────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_execution_plan(self, executor, mock_page):
        plan = MagicMock()
        plan.steps = []
        results = executor.execute_plan(mock_page, plan)
        assert len(results) == 0

    def test_submission_report_generates_uuid(self):
        r1 = SubmissionReport()
        r2 = SubmissionReport()
        assert r1.report_id != r2.report_id

    def test_step_execution_tracks_duration(self, executor, mock_page, mock_step):
        result = executor.execute_step(mock_page, mock_step)
        assert result.duration_ms is not None
        assert result.duration_ms >= 0

    def test_state_machine_transition_updates_timestamp(self, state_machine):
        status = SubmissionStatus(package_id="pkg-1")
        before = status.updated_at
        import time
        time.sleep(0.01)
        state_machine.transition(status, SubmissionState.VALIDATING)
        assert status.updated_at > before

    def test_recovery_compute_delay_backoff(self, recovery):
        d1 = recovery._compute_delay(1)
        d2 = recovery._compute_delay(2)
        assert d2 > d1
        assert d2 == d1 * recovery._config.backoff_multiplier

    def test_safety_checks_dry_run(self, safety):
        safety.set_mode(ExecutionMode.DRY_RUN)
        checks = safety.check(ExecutionMode.DRY_RUN)
        assert all(isinstance(c, SafetyCheck) for c in checks)

    def test_metrics_accumulates(self, metrics_tracker):
        for i in range(5):
            step = StepExecution(
                step_type=SubmissionStepType.FILL,
                field_ref=f"f{i}",
                result=SubmissionStepResult.SUCCESS,
                duration_ms=10.0,
            )
            metrics_tracker.record_step(step)
        metrics = metrics_tracker.get_metrics()
        assert metrics.total_fields == 5
        assert metrics.field_execution_duration_ms == 50.0

    def test_validator_pre_submit_upload_failures(self, validator):
        status = SubmissionStatus(package_id="pkg-1", state=SubmissionState.EXECUTING_UPLOADS)
        plan = MagicMock()
        plan.steps = []
        upload_result = MagicMock()
        upload_result.result = type("Result", (), {"value": "failed"})()
        upload_result.field_ref = "resume"
        issues = validator.validate_pre_submit(status, plan, upload_results=[upload_result])
        assert any("upload" in i.lower() for i in issues)

    def test_orchestrator_safe_retry_exhausted(self, mock_page, mock_execution_plan):
        failing_provider = MagicMock()
        failing_provider.name = "failing"
        failing_provider.submit.side_effect = Exception("server error")
        failing_provider.confirm.side_effect = Exception("confirm error")

        orch = SubmissionOrchestratorEngine()
        report = orch.run(mock_page, mock_execution_plan, mode=ExecutionMode.SAFE_RETRY, provider=failing_provider)
        assert report.status == "failed"

    def test_provider_confirm_detects_duplicate(self):
        provider = BaseSubmissionProvider("test")
        page = MagicMock()
        page.url = "https://example.com/apply"
        page.text_content.return_value = "You have already applied for this job"
        result = provider.confirm(page, 1000)
        assert result.duplicate_detected is True

    def test_provider_confirm_extracts_application_id(self):
        provider = BaseSubmissionProvider("test")
        page = MagicMock()
        page.url = "https://example.com/apply"
        page.text_content.return_value = "Application number: APP-999 has been submitted"
        result = provider.confirm(page, 1000)
        assert result.success_page_detected is True

    def test_provider_submit_visible_button(self):
        provider = BaseSubmissionProvider("test")
        page = MagicMock()
        btn = MagicMock()
        btn.is_visible.return_value = True
        page.locator.return_value = btn
        result = provider.submit(page, 1000)
        assert result is True

    def test_provider_submit_no_visible_button(self):
        provider = BaseSubmissionProvider("test")
        page = MagicMock()
        btn = MagicMock()
        btn.is_visible.return_value = False
        page.locator.return_value = btn
        result = provider.submit(page, 1000)
        assert result is False

    def test_state_machine_failed_to_pending(self, state_machine):
        status = SubmissionStatus(package_id="pkg-1", state=SubmissionState.FAILED)
        result = state_machine.transition(status, SubmissionState.PENDING)
        assert result.state == SubmissionState.PENDING
