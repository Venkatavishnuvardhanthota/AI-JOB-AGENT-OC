from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.uploads.capabilities import UploadCapabilityAnalyzer
from app.uploads.config import UploadsConfig
from app.uploads.dependencies import (
    get_uploads_config,
    get_uploads_factory,
    get_uploads_registry,
    get_uploads_service,
    reset_uploads_service,
)
from app.uploads.exceptions import (
    UploadCapabilityError,
    UploadConfigError,
    UploadError,
    UploadExecutionError,
    UploadProviderNotFoundError,
    UploadRejectedError,
    UploadTimeoutError,
    UploadValidationError,
    UploadVerificationError,
)
from app.uploads.executor import UploadExecutorEngine
from app.uploads.factory import UploadProviderFactory
from app.uploads.manager import UploadManager
from app.uploads.normalization import lookup_document_type, normalize_label
from app.uploads.planner import UploadPlannerEngine
from app.uploads.providers.base import BaseUploadProvider
from app.uploads.registry import UploadProviderRegistry
from app.uploads.schemas import (
    DocumentType,
    ProviderCapabilities,
    RetryPolicy,
    UploadAttempt,
    UploadFieldInfo,
    UploadPlan,
    UploadRequest,
    UploadResult,
    UploadSource,
    UploadSummary,
    UploadTask,
    UploadTaskResult,
    UploadTaskType,
    VerificationPolicy,
    VerificationResult,
)
from app.uploads.service import DocumentUploadService
from app.uploads.validator import DocumentValidator
from app.uploads.verification import UploadVerifierEngine

# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def config() -> UploadsConfig:
    return UploadsConfig()


@pytest.fixture
def registry() -> UploadProviderRegistry:
    return UploadProviderRegistry()


@pytest.fixture
def factory(registry) -> UploadProviderFactory:
    return UploadProviderFactory(registry=registry)


@pytest.fixture
def service(registry, factory, config) -> DocumentUploadService:
    return DocumentUploadService(registry=registry, factory=factory, config=config)


@pytest.fixture
def validator() -> DocumentValidator:
    return DocumentValidator()


@pytest.fixture
def planner() -> UploadPlannerEngine:
    return UploadPlannerEngine()


@pytest.fixture
def executor() -> UploadExecutorEngine:
    return UploadExecutorEngine()


@pytest.fixture
def verifier() -> UploadVerifierEngine:
    return UploadVerifierEngine()


@pytest.fixture
def manager() -> UploadManager:
    return UploadManager()


@pytest.fixture
def mock_page() -> MagicMock:
    page = MagicMock()
    element = MagicMock()
    element.is_visible.return_value = True
    element.get_attribute.return_value = None
    page.locator.return_value = element
    return page


@pytest.fixture
def mock_execution_plan() -> MagicMock:
    plan = MagicMock()
    plan.plan_id = "plan-1"

    upload_step = MagicMock()
    upload_step.step_type = type("StepType", (), {"value": "upload"})()
    upload_step.field_ref = "resume-upload"
    upload_step.selector = "#resume-input"
    upload_step.reason = "Upload resume"
    upload_step.requires_manual_review = False
    upload_step.source_path = "/path/to/resume.pdf"

    skip_step = MagicMock()
    skip_step.step_type = type("StepType", (), {"value": "skip"})()
    skip_step.field_ref = "optional-doc"
    skip_step.selector = "#optional"
    skip_step.reason = "Not available"
    skip_step.requires_manual_review = False
    skip_step.source_path = None

    manual_step = MagicMock()
    manual_step.step_type = type("StepType", (), {"value": "request_manual"})()
    manual_step.field_ref = "cover-letter"
    manual_step.selector = "#cl-input"
    manual_step.reason = "Manual upload required"
    manual_step.requires_manual_review = True
    manual_step.source_path = None

    plan.steps = [upload_step, skip_step, manual_step]
    return plan


@pytest.fixture
def temp_file(tmp_path):
    file = tmp_path / "test_resume.pdf"
    file.write_text("fake pdf content")
    return str(file)


# ─── Test Exceptions ─────────────────────────────────────────────────────────


class TestUploadsExceptions:
    def test_upload_error(self):
        err = UploadError("test error")
        assert err.message == "test error"
        assert err.code == "UPLOAD_ERROR"

    def test_validation_error(self):
        err = UploadValidationError("invalid")
        assert err.code == "UPLOAD_VALIDATION_ERROR"
        assert err.status_code == 400

    def test_execution_error(self):
        err = UploadExecutionError("failed")
        assert err.code == "UPLOAD_EXECUTION_ERROR"

    def test_verification_error(self):
        err = UploadVerificationError("verify failed")
        assert err.code == "UPLOAD_VERIFICATION_ERROR"

    def test_capability_error(self):
        err = UploadCapabilityError("not supported")
        assert err.code == "UPLOAD_CAPABILITY_ERROR"

    def test_timeout_error(self):
        err = UploadTimeoutError("timed out")
        assert err.code == "UPLOAD_TIMEOUT_ERROR"

    def test_rejected_error(self):
        err = UploadRejectedError("rejected")
        assert err.code == "UPLOAD_REJECTED_ERROR"
        assert err.status_code == 400

    def test_provider_not_found(self):
        err = UploadProviderNotFoundError("not found")
        assert err.code == "UPLOAD_PROVIDER_NOT_FOUND"
        assert err.status_code == 404

    def test_config_error(self):
        err = UploadConfigError("bad config")
        assert err.code == "UPLOAD_CONFIG_ERROR"


# ─── Test Config ─────────────────────────────────────────────────────────────


class TestUploadsConfig:
    def test_defaults(self):
        cfg = UploadsConfig()
        assert cfg.max_file_size_mb == 25
        assert cfg.default_timeout_ms == 60000.0
        assert cfg.retry_attempts == 3
        assert cfg.verify_after_upload is True
        assert ".pdf" in cfg.allowed_extensions
        assert "application/pdf" in cfg.allowed_mime_types

    def test_document_type_extensions(self):
        cfg = UploadsConfig()
        assert ".pdf" in cfg.document_type_extensions["resume"]
        assert ".docx" in cfg.document_type_extensions["cover_letter"]

    def test_document_type_mimes(self):
        cfg = UploadsConfig()
        assert "application/pdf" in cfg.document_type_mimes["resume"]


# ─── Test Schemas ────────────────────────────────────────────────────────────


class TestSchemas:
    def test_document_type_enum(self):
        assert DocumentType.RESUME.value == "resume"
        assert DocumentType.COVER_LETTER.value == "cover_letter"
        assert len(DocumentType) == 8

    def test_upload_field_info_defaults(self):
        info = UploadFieldInfo(selector="#file")
        assert info.selector == "#file"
        assert info.accepted_mime_types == []
        assert info.multiple is False
        assert info.required is False

    def test_upload_source(self):
        src = UploadSource(path="/path/to/file.pdf", document_type=DocumentType.RESUME)
        assert src.path == "/path/to/file.pdf"
        assert src.document_type == DocumentType.RESUME

    def test_upload_task_defaults(self):
        task = UploadTask(field_ref="f1", document_type=DocumentType.RESUME)
        assert task.task_type == UploadTaskType.UPLOAD
        assert task.retry_policy.max_attempts == 3
        assert task.verification_policy.verify_after_upload is True

    def test_upload_plan(self):
        task = UploadTask(field_ref="f1", document_type=DocumentType.RESUME)
        plan = UploadPlan(tasks=[task])
        assert len(plan.tasks) == 1
        assert plan.execution_plan_ref is None

    def test_upload_result(self):
        result = UploadResult(task_id="t1", field_ref="f1", result=UploadTaskResult.SUCCESS)
        assert result.verified is False

    def test_upload_summary(self):
        summary = UploadSummary(plan_id="p1")
        assert summary.total == 0

    def test_provider_capabilities_defaults(self):
        caps = ProviderCapabilities(provider_name="test")
        assert caps.supports_single_file is True
        assert caps.supports_multiple_files is False

    def test_verification_result_defaults(self):
        vr = VerificationResult()
        assert vr.verified is False
        assert vr.error_messages_found == []

    def test_retry_policy(self):
        rp = RetryPolicy()
        assert rp.max_attempts == 3
        assert rp.backoff_multiplier == 2.0

    def test_upload_attempt(self):
        attempt = UploadAttempt(attempt_number=1, result=UploadTaskResult.SUCCESS)
        assert attempt.error_message is None

    def test_upload_request(self):
        req = UploadRequest(document_type=DocumentType.RESUME, file_path="/path/file.pdf")
        assert req.document_type == DocumentType.RESUME

    def test_upload_task_type_enum(self):
        assert UploadTaskType.UPLOAD.value == "upload"
        assert UploadTaskType.SKIP.value == "skip"
        assert UploadTaskType.MANUAL.value == "manual"

    def test_upload_task_result_enum(self):
        assert UploadTaskResult.PENDING.value == "pending"
        assert UploadTaskResult.SUCCESS.value == "success"


# ─── Test Normalization ──────────────────────────────────────────────────────


class TestNormalization:
    def test_normalize_label_lowercase(self):
        assert normalize_label("RESUME") == "resume"

    def test_normalize_label_strip_colon(self):
        assert normalize_label("Resume:") == "resume"

    def test_normalize_label_collapse_spaces(self):
        assert normalize_label("  Cover   Letter  ") == "cover letter"

    def test_lookup_resume(self):
        assert lookup_document_type("Upload your Resume") == DocumentType.RESUME

    def test_lookup_cover_letter(self):
        assert lookup_document_type("Cover Letter") == DocumentType.COVER_LETTER

    def test_lookup_portfolio(self):
        assert lookup_document_type("Portfolio URL") == DocumentType.PORTFOLIO

    def test_lookup_transcript(self):
        assert lookup_document_type("Transcript of records") == DocumentType.TRANSCRIPT

    def test_lookup_certificate(self):
        assert lookup_document_type("Certification") == DocumentType.CERTIFICATE

    def test_lookup_custom_default(self):
        assert lookup_document_type("Some random field") == DocumentType.CUSTOM

    def test_lookup_cv(self):
        assert lookup_document_type("Upload CV") == DocumentType.RESUME


# ─── Test Capabilities ───────────────────────────────────────────────────────


class TestCapabilities:
    def test_analyze_no_page(self):
        analyzer = UploadCapabilityAnalyzer()
        info = analyzer.analyze(None, "#file")
        assert info.selector == "#file"
        assert info.multiple is False

    def test_analyze_with_page(self, mock_page):
        analyzer = UploadCapabilityAnalyzer()
        info = analyzer.analyze(mock_page, "#file")
        assert info.selector == "#file"

    def test_get_provider_caps_greenhouse(self):
        analyzer = UploadCapabilityAnalyzer()
        caps = analyzer.get_provider_capabilities("greenhouse")
        assert caps.max_file_size_mb == 10.0
        assert caps.supports_multiple_files is False

    def test_get_provider_caps_lever(self):
        analyzer = UploadCapabilityAnalyzer()
        caps = analyzer.get_provider_capabilities("lever")
        assert caps.supports_multiple_files is True
        assert caps.supports_drag_and_drop is True

    def test_get_provider_caps_ashby(self):
        analyzer = UploadCapabilityAnalyzer()
        caps = analyzer.get_provider_capabilities("ashby")
        assert caps.supports_drag_and_drop is True
        assert caps.supports_multiple_files is False

    def test_get_provider_caps_workday(self):
        analyzer = UploadCapabilityAnalyzer()
        caps = analyzer.get_provider_capabilities("workday")
        assert caps.supports_replace is True

    def test_get_provider_caps_default(self):
        analyzer = UploadCapabilityAnalyzer()
        caps = analyzer.get_provider_capabilities("default")
        assert caps.supports_multiple_files is False
        assert caps.max_file_size_mb == 10.0

    def test_analyze_with_accept_attribute(self, mock_page):
        element = mock_page.locator.return_value
        element.get_attribute.side_effect = lambda attr: ".pdf,.doc,.docx" if attr == "accept" else None
        analyzer = UploadCapabilityAnalyzer()
        info = analyzer.analyze(mock_page, "#file")
        assert ".pdf" in info.accepted_extensions

    def test_analyze_with_multiple(self, mock_page):
        element = mock_page.locator.return_value
        element.get_attribute.side_effect = lambda attr: "true" if attr == "multiple" else None
        analyzer = UploadCapabilityAnalyzer()
        info = analyzer.analyze(mock_page, "#file")
        assert info.multiple is True

    def test_analyze_with_required(self, mock_page):
        element = mock_page.locator.return_value
        element.get_attribute.side_effect = lambda attr: "true" if attr == "required" else None
        analyzer = UploadCapabilityAnalyzer()
        info = analyzer.analyze(mock_page, "#file")
        assert info.required is True


# ─── Test Validator ──────────────────────────────────────────────────────────


class TestValidator:
    def test_validate_empty_path(self, validator):
        issues = validator.validate_file("", DocumentType.RESUME)
        assert "File path is empty" in issues

    def test_validate_nonexistent(self, validator):
        issues = validator.validate_file("/nonexistent/file.pdf", DocumentType.RESUME)
        assert any("does not exist" in i for i in issues)

    def test_validate_valid_file(self, validator, temp_file):
        issues = validator.validate_file(temp_file, DocumentType.RESUME)
        assert len(issues) == 0

    def test_validate_empty_file(self, tmp_path, validator):
        empty = tmp_path / "empty.pdf"
        empty.write_text("")
        issues = validator.validate_file(str(empty), DocumentType.RESUME)
        assert any("empty" in i for i in issues)

    def test_validate_wrong_extension(self, tmp_path, validator):
        f = tmp_path / "resume.exe"
        f.write_text("content")
        issues = validator.validate_file(str(f), DocumentType.RESUME)
        assert any("extension" in i.lower() for i in issues)

    def test_validate_plan_empty(self, validator):
        plan = UploadPlan()
        issues = validator.validate_plan(plan)
        assert "no tasks" in issues

    def test_validate_plan_duplicate_refs(self, validator):
        task1 = UploadTask(field_ref="f1", document_type=DocumentType.RESUME)
        task2 = UploadTask(field_ref="f1", document_type=DocumentType.COVER_LETTER)
        plan = UploadPlan(tasks=[task1, task2])
        issues = validator.validate_plan(plan)
        assert any("duplicate" in i.lower() for i in issues)

    def test_validate_plan_valid(self, validator):
        src = UploadSource(path="/path/f.pdf", document_type=DocumentType.RESUME)
        task = UploadTask(field_ref="f1", selector="#file", document_type=DocumentType.RESUME, source=src)
        plan = UploadPlan(tasks=[task])
        issues = validator.validate_plan(plan)
        assert len(issues) == 0

    def test_validate_plan_missing_selector(self, validator):
        task = UploadTask(field_ref="f1", selector="", document_type=DocumentType.RESUME)
        plan = UploadPlan(tasks=[task])
        issues = validator.validate_plan(plan)
        assert any("selector" in i for i in issues)

    def test_validate_file_upload_raises(self, validator, temp_file):
        result = validator.validate_file_upload(temp_file, DocumentType.RESUME)
        assert result["valid"] is True

    def test_validate_file_upload_invalid_raises(self, validator):
        with pytest.raises(UploadValidationError):
            validator.validate_file_upload("", DocumentType.RESUME)


# ─── Test Planner ────────────────────────────────────────────────────────────


class TestPlanner:
    def test_plan_empty(self, planner):
        plan = MagicMock()
        plan.steps = []
        upload_plan = planner.plan(plan)
        assert len(upload_plan.tasks) == 0
        assert upload_plan.total_tasks == 0

    def test_plan_with_steps(self, planner, mock_execution_plan):
        upload_plan = planner.plan(mock_execution_plan)
        assert len(upload_plan.tasks) == 3

    def test_plan_tallies(self, planner, mock_execution_plan):
        upload_plan = planner.plan(mock_execution_plan)
        assert upload_plan.upload_tasks == 1
        assert upload_plan.skip_tasks == 1
        assert upload_plan.manual_tasks == 1

    def test_plan_creates_upload_task(self, planner, mock_execution_plan):
        upload_plan = planner.plan(mock_execution_plan)
        upload_tasks = [t for t in upload_plan.tasks if t.task_type == UploadTaskType.UPLOAD]
        assert len(upload_tasks) == 1
        task = upload_tasks[0]
        assert task.field_ref == "resume-upload"
        assert task.selector == "#resume-input"
        assert task.document_type == DocumentType.RESUME
        assert task.source is not None

    def test_plan_detects_document_type_from_reason(self, planner):
        plan = MagicMock()
        step = MagicMock()
        step.step_type = type("StepType", (), {"value": "upload"})()
        step.field_ref = "f1"
        step.selector = "#f1"
        step.reason = "Upload cover letter"
        step.requires_manual_review = False
        step.source_path = "/path/doc.pdf"
        plan.steps = [step]
        upload_plan = planner.plan(plan)
        assert upload_plan.tasks[0].document_type == DocumentType.COVER_LETTER

    def test_plan_detects_document_type_from_path(self, planner):
        plan = MagicMock()
        step = MagicMock()
        step.step_type = type("StepType", (), {"value": "upload"})()
        step.field_ref = "f1"
        step.selector = "#f1"
        step.reason = "Upload document"
        step.requires_manual_review = False
        step.source_path = "/path/my_resume.pdf"
        plan.steps = [step]
        upload_plan = planner.plan(plan)
        assert upload_plan.tasks[0].document_type == DocumentType.RESUME

    def test_plan_creates_skip_task(self, planner, mock_execution_plan):
        upload_plan = planner.plan(mock_execution_plan)
        skip_tasks = [t for t in upload_plan.tasks if t.task_type == UploadTaskType.SKIP]
        assert len(skip_tasks) == 1
        assert skip_tasks[0].field_ref == "optional-doc"

    def test_plan_creates_manual_task(self, planner, mock_execution_plan):
        upload_plan = planner.plan(mock_execution_plan)
        manual_tasks = [t for t in upload_plan.tasks if t.task_type == UploadTaskType.MANUAL]
        assert len(manual_tasks) == 1
        assert manual_tasks[0].requires_manual_review is True


# ─── Test Executor ───────────────────────────────────────────────────────────


class TestExecutor:
    def test_execute_skip_task(self, executor, mock_page):
        task = UploadTask(
            task_type=UploadTaskType.SKIP,
            field_ref="f1",
            document_type=DocumentType.RESUME,
        )
        result = executor.execute_task(mock_page, task)
        assert result.result == UploadTaskResult.SKIPPED

    def test_execute_manual_task(self, executor, mock_page):
        task = UploadTask(
            task_type=UploadTaskType.MANUAL,
            field_ref="f1",
            document_type=DocumentType.RESUME,
        )
        result = executor.execute_task(mock_page, task)
        assert result.result == UploadTaskResult.MANUAL_REQUIRED

    def test_execute_upload_no_source(self, executor, mock_page):
        task = UploadTask(
            task_type=UploadTaskType.UPLOAD,
            field_ref="f1",
            selector="#file",
            document_type=DocumentType.RESUME,
        )
        result = executor.execute_task(mock_page, task)
        assert result.result == UploadTaskResult.FAILED
        assert "No source file" in (result.final_error or "")

    def test_execute_upload_success(self, executor, mock_page, temp_file):
        task = UploadTask(
            task_type=UploadTaskType.UPLOAD,
            field_ref="f1",
            selector="#file",
            document_type=DocumentType.RESUME,
            source=UploadSource(path=temp_file, document_type=DocumentType.RESUME),
        )
        result = executor.execute_task(mock_page, task)
        assert result.result == UploadTaskResult.SUCCESS
        assert len(result.attempts) == 1
        assert result.attempts[0].result == UploadTaskResult.SUCCESS

    def test_execute_upload_element_not_visible(self, executor, mock_page, temp_file):
        element = mock_page.locator.return_value
        element.is_visible.return_value = False
        task = UploadTask(
            task_type=UploadTaskType.UPLOAD,
            field_ref="f1",
            selector="#file",
            document_type=DocumentType.RESUME,
            source=UploadSource(path=temp_file, document_type=DocumentType.RESUME),
        )
        result = executor.execute_task(mock_page, task)
        assert result.result == UploadTaskResult.FAILED
        assert "not visible" in (result.final_error or "")

    def test_execute_upload_retry_then_success(self, executor, mock_page, temp_file):
        element = mock_page.locator.return_value
        element.is_visible.side_effect = [False, True]

        task = UploadTask(
            task_type=UploadTaskType.UPLOAD,
            field_ref="f1",
            selector="#file",
            document_type=DocumentType.RESUME,
            source=UploadSource(path=temp_file, document_type=DocumentType.RESUME),
            retry_policy=RetryPolicy(max_attempts=2, delay_seconds=0.01),
        )
        result = executor.execute_task(mock_page, task)
        assert result.result == UploadTaskResult.SUCCESS

    def test_execute_upload_all_retries_fail(self, executor, mock_page, temp_file):
        element = mock_page.locator.return_value
        element.is_visible.side_effect = [False, False, False]

        task = UploadTask(
            task_type=UploadTaskType.UPLOAD,
            field_ref="f1",
            selector="#file",
            document_type=DocumentType.RESUME,
            source=UploadSource(path=temp_file, document_type=DocumentType.RESUME),
            retry_policy=RetryPolicy(max_attempts=3, delay_seconds=0.01),
        )
        result = executor.execute_task(mock_page, task)
        assert result.result == UploadTaskResult.FAILED

    def test_execute_plan(self, executor, mock_page, temp_file):
        task = UploadTask(
            task_type=UploadTaskType.UPLOAD,
            field_ref="f1",
            selector="#file",
            document_type=DocumentType.RESUME,
            source=UploadSource(path=temp_file, document_type=DocumentType.RESUME),
        )
        plan = UploadPlan(tasks=[task])
        results = executor.execute(mock_page, plan)
        assert len(results) == 1
        assert results[0].result == UploadTaskResult.SUCCESS

    def test_compute_delay(self, executor):
        task = UploadTask(field_ref="f1", document_type=DocumentType.RESUME)
        delay = executor._compute_delay(1, task)
        assert delay == task.retry_policy.delay_seconds
        delay2 = executor._compute_delay(2, task)
        assert delay2 == task.retry_policy.delay_seconds * task.retry_policy.backoff_multiplier

    def test_execute_upload_timeout(self, executor, mock_page, temp_file):
        element = mock_page.locator.return_value
        element.is_visible.side_effect = Exception("timeout exceeded")

        task = UploadTask(
            task_type=UploadTaskType.UPLOAD,
            field_ref="f1",
            selector="#file",
            document_type=DocumentType.RESUME,
            source=UploadSource(path=temp_file, document_type=DocumentType.RESUME),
            retry_policy=RetryPolicy(max_attempts=2, delay_seconds=0.01),
        )
        result = executor.execute_task(mock_page, task)
        # "timeout" in error → UploadTimeoutError but we catch generic Exception too
        assert result.result in (UploadTaskResult.TIMEOUT, UploadTaskResult.FAILED)

    def test_execute_upload_rejected(self, executor, mock_page, temp_file):
        element = mock_page.locator.return_value
        element.is_visible.side_effect = Exception("File type not allowed")

        task = UploadTask(
            task_type=UploadTaskType.UPLOAD,
            field_ref="f1",
            selector="#file",
            document_type=DocumentType.RESUME,
            source=UploadSource(path=temp_file, document_type=DocumentType.RESUME),
        )
        result = executor.execute_task(mock_page, task)
        assert result.result in (UploadTaskResult.FAILED, UploadTaskResult.REJECTED)


# ─── Test Verification ───────────────────────────────────────────────────────


class TestVerification:
    def test_verify_no_page(self, verifier):
        task = UploadTask(field_ref="f1", document_type=DocumentType.RESUME, selector="#file")
        result = verifier.verify(None, task)
        assert result.verified is False
        assert "page is not available" in result.details.lower()

    def test_verify_visible_element(self, verifier, mock_page):
        task = UploadTask(field_ref="f1", document_type=DocumentType.RESUME, selector="#file")
        result = verifier.verify(mock_page, task)
        assert result.verified is True

    def test_verify_hidden_element(self, verifier, mock_page):
        element = mock_page.locator.return_value
        element.is_visible.return_value = False
        task = UploadTask(field_ref="f1", document_type=DocumentType.RESUME, selector="#file")
        result = verifier.verify(mock_page, task)
        assert result.verified is True
        assert result.element_state_valid is False

    def test_verify_with_error_messages(self, verifier, mock_page):
        element = mock_page.locator.return_value
        element.is_visible.return_value = True

        parent = MagicMock()
        parent.text_content.return_value = "error: file too large"
        element.locator.return_value = parent

        task = UploadTask(field_ref="f1", document_type=DocumentType.RESUME, selector="#file")
        result = verifier.verify(mock_page, task)
        assert len(result.error_messages_found) > 0

    def test_verify_with_completion_indicator(self, verifier, mock_page):
        element = mock_page.locator.return_value
        element.is_visible.return_value = True

        parent = MagicMock()
        parent.text_content.return_value = "File uploaded successfully ✓"
        element.locator.return_value = parent

        task = UploadTask(field_ref="f1", document_type=DocumentType.RESUME, selector="#file")
        result = verifier.verify(mock_page, task)
        assert result.completion_indicator_found is True

    def test_verify_exception_handling(self, verifier, mock_page):
        mock_page.locator.side_effect = Exception("element detached")
        task = UploadTask(field_ref="f1", document_type=DocumentType.RESUME, selector="#file")
        result = verifier.verify(mock_page, task)
        assert result.verified is True


# ─── Test Manager ────────────────────────────────────────────────────────────


class TestManager:
    def test_create_plan(self, manager, mock_execution_plan):
        plan = manager.create_plan(mock_execution_plan)
        assert len(plan.tasks) == 3

    def test_execute_plan(self, manager, mock_page, temp_file, mock_execution_plan):
        plan = manager.create_plan(mock_execution_plan)
        results = manager.execute_plan(mock_page, plan)
        assert len(results) == 3

    def test_validate_document(self, manager, temp_file):
        issues = manager.validate_document(temp_file, DocumentType.RESUME)
        assert len(issues) == 0

    def test_validate_document_invalid(self, manager):
        issues = manager.validate_document("", DocumentType.RESUME)
        assert len(issues) > 0

    def test_analyze_field(self, manager, mock_page):
        info = manager.analyze_field(mock_page, "#file")
        assert info.selector == "#file"

    def test_verify_upload(self, manager, mock_page):
        task = UploadTask(field_ref="f1", document_type=DocumentType.RESUME, selector="#file")
        result = manager.verify_upload(mock_page, task)
        assert result is not None

    def test_summarize_empty(self, manager):
        summary = manager.summarize([])
        assert summary.total == 0

    def test_summarize_results(self, manager):
        results = [
            UploadResult(task_id="t1", field_ref="f1", result=UploadTaskResult.SUCCESS, duration_ms=100.0),
            UploadResult(task_id="t2", field_ref="f2", result=UploadTaskResult.SKIPPED),
            UploadResult(task_id="t3", field_ref="f3", result=UploadTaskResult.FAILED, duration_ms=50.0),
        ]
        summary = manager.summarize(results)
        assert summary.total == 3
        assert summary.success == 1
        assert summary.skipped == 1
        assert summary.failed == 1
        assert summary.total_duration_ms == 150.0


# ─── Test Registry ───────────────────────────────────────────────────────────


class TestUploadRegistry:
    def test_register_and_resolve(self, registry):
        provider = BaseUploadProvider("test")
        registry.register("test", provider)
        assert registry.is_registered("test")
        assert registry.resolve("test") == provider

    def test_resolve_not_found(self, registry):
        with pytest.raises(UploadProviderNotFoundError):
            registry.resolve("nonexistent")

    def test_register_duplicate(self, registry):
        registry.register("p1", BaseUploadProvider("p1"))
        registry.register("p1", BaseUploadProvider("p1-2"))
        assert registry.count() == 1

    def test_unregister(self, registry):
        registry.register("p1", BaseUploadProvider("p1"))
        registry.unregister("p1")
        assert not registry.is_registered("p1")

    def test_list_providers(self, registry):
        registry.register("a", BaseUploadProvider("a"))
        registry.register("b", BaseUploadProvider("b"))
        assert "a" in registry.list_providers()
        assert "b" in registry.list_providers()

    def test_count(self, registry):
        assert registry.count() == 0
        registry.register("p1", BaseUploadProvider("p1"))
        assert registry.count() == 1

    def test_clear(self, registry):
        registry.register("p1", BaseUploadProvider("p1"))
        registry.clear()
        assert registry.count() == 0


# ─── Test Factory ────────────────────────────────────────────────────────────


class TestUploadFactory:
    def test_create_provider(self, registry):
        factory = UploadProviderFactory(registry=registry)
        provider = factory.create_provider("custom")
        assert registry.is_registered("custom")
        assert provider.name == "custom"

    def test_register_all(self, registry):
        factory = UploadProviderFactory(registry=registry)
        factory.register_all()
        names = ["greenhouse", "lever", "ashby", "workday", "smartrecruiters", "bamboohr", "recruitee"]
        for name in names:
            assert registry.is_registered(name)

    def test_register_all_skips_existing(self, registry):
        factory = UploadProviderFactory(registry=registry)
        registry.register("greenhouse", BaseUploadProvider("greenhouse"))
        factory.register_all()
        assert registry.count() == 7

    def test_detect_provider(self, registry):
        factory = UploadProviderFactory(registry=registry)
        provider = BaseUploadProvider("test")
        registry.register("test", provider)
        detected = factory.detect_provider("https://example.com")
        assert detected == provider


# ─── Test Service ────────────────────────────────────────────────────────────


class TestUploadService:
    def test_create_upload_plan(self, service, mock_execution_plan):
        plan = service.create_upload_plan(mock_execution_plan)
        assert len(plan.tasks) == 3

    def test_validate_document_valid(self, service, temp_file):
        issues = service.validate_document(temp_file, DocumentType.RESUME)
        assert len(issues) == 0

    def test_validate_and_raise_valid(self, service, temp_file):
        service.validate_and_raise(temp_file, DocumentType.RESUME)

    def test_validate_and_raise_invalid(self, service):
        with pytest.raises(UploadValidationError):
            service.validate_and_raise("", DocumentType.RESUME)

    def test_get_provider_capabilities(self, service):
        caps = service.get_provider_capabilities("lever")
        assert caps.supports_multiple_files is True

    def test_detect_provider(self, service, registry):
        registry.register("default", BaseUploadProvider("default"))
        name = service.detect_provider("https://example.com")
        assert name == "default"

    def test_get_provider_for_url_default(self, service):
        provider = service.get_provider_for_url("https://example.com")
        assert provider is not None

    def test_execute_and_summarize(self, service, mock_page, temp_file, mock_execution_plan):
        plan = service.create_upload_plan(mock_execution_plan)
        results, summary = service.execute_and_summarize(mock_page, plan)
        assert len(results) == 3
        assert summary.total == 3

    def test_analyze_upload_field(self, service, mock_page):
        info = service.analyze_upload_field(mock_page, "#file")
        assert info.selector == "#file"


# ─── Test Dependencies ───────────────────────────────────────────────────────


class TestUploadsDependencies:
    def test_get_config(self):
        cfg = get_uploads_config()
        assert isinstance(cfg, UploadsConfig)

    def test_get_registry(self):
        reg = get_uploads_registry()
        assert isinstance(reg, UploadProviderRegistry)
        reset_uploads_service()

    def test_get_registry_singleton(self):
        reg1 = get_uploads_registry()
        reg2 = get_uploads_registry()
        assert reg1 is reg2
        reset_uploads_service()

    def test_get_factory(self):
        factory = get_uploads_factory()
        assert isinstance(factory, UploadProviderFactory)
        reset_uploads_service()

    def test_get_service(self):
        service = get_uploads_service()
        assert isinstance(service, DocumentUploadService)
        reset_uploads_service()

    def test_get_service_singleton(self):
        s1 = get_uploads_service()
        s2 = get_uploads_service()
        assert s1 is s2
        reset_uploads_service()

    def test_reset_service(self):
        s1 = get_uploads_service()
        reset_uploads_service()
        s2 = get_uploads_service()
        assert s1 is not s2
        reset_uploads_service()

    def test_get_service_initializes_providers(self):
        service = get_uploads_service()
        assert service._registry.count() > 0
        reset_uploads_service()


# ─── Test BaseUploadProvider ─────────────────────────────────────────────────


class TestBaseUploadProvider:
    def test_supports(self):
        provider = BaseUploadProvider("test")
        assert provider.supports("https://example.com") is True

    def test_get_capabilities(self):
        provider = BaseUploadProvider("test")
        caps = provider.get_capabilities()
        assert caps.provider_name == "test"
        assert caps.max_file_size_mb == 10.0

    def test_name_property(self):
        provider = BaseUploadProvider("my-provider")
        assert provider.name == "my-provider"


# ─── Test Edge Cases ─────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_plan_tasks(self):
        plan = UploadPlan()
        assert len(plan.tasks) == 0

    def test_upload_summary_all_zeros(self):
        summary = UploadSummary(plan_id="empty")
        assert summary.total == 0

    def test_upload_task_generates_uuid(self):
        task1 = UploadTask(field_ref="f1", document_type=DocumentType.RESUME)
        task2 = UploadTask(field_ref="f1", document_type=DocumentType.RESUME)
        assert task1.task_id != task2.task_id

    def test_verify_with_nearby_filename(self, verifier, mock_page):
        element = mock_page.locator.return_value
        element.is_visible.return_value = True

        nearby = MagicMock()
        nearby.text_content.return_value = "resume.pdf"
        element.locator.return_value = nearby

        task = UploadTask(field_ref="f1", document_type=DocumentType.RESUME, selector="#file")
        result = verifier.verify(mock_page, task)
        assert result.filename_displayed or result.verified

    def test_upload_field_info_mime_types(self):
        info = UploadFieldInfo(
            selector="#file",
            accepted_mime_types=["application/pdf"],
            accepted_extensions=[".pdf"],
            multiple=True,
        )
        assert "application/pdf" in info.accepted_mime_types
        assert ".pdf" in info.accepted_extensions

    def test_upload_source_no_filename(self):
        src = UploadSource(path="/path/to/doc.pdf", document_type=DocumentType.RESUME)
        assert src.original_filename is None

    def test_provider_capabilities_limitations(self):
        caps = ProviderCapabilities(
            provider_name="test",
            limitations=["Max 10MB", "No drag-and-drop"],
        )
        assert len(caps.limitations) == 2

    def test_verification_policy_defaults(self):
        policy = VerificationPolicy()
        assert policy.verify_after_upload is True
        assert policy.check_filename_displayed is True

    def test_retry_policy_backoff(self):
        policy = RetryPolicy(max_attempts=5, backoff_multiplier=3.0)
        assert policy.backoff_multiplier == 3.0

    def test_upload_result_no_attempts(self):
        result = UploadResult(task_id="t1", field_ref="f1", result=UploadTaskResult.PENDING)
        assert len(result.attempts) == 0

    def test_upload_task_manual_requires_review(self):
        task = UploadTask(
            task_type=UploadTaskType.MANUAL,
            field_ref="f1",
            document_type=DocumentType.CUSTOM,
            requires_manual_review=True,
        )
        assert task.requires_manual_review is True

    def test_normalize_label_with_special_chars(self):
        assert normalize_label("Resume (PDF)*") == "resume pdf"

    def test_lookup_document_type_case_insensitive(self):
        assert lookup_document_type("UPLOAD YOUR RESUME") == DocumentType.RESUME

    def test_planner_default_document_type(self, planner):
        plan = MagicMock()
        step = MagicMock()
        step.step_type = type("StepType", (), {"value": "upload"})()
        step.field_ref = "f1"
        step.selector = "#f1"
        step.reason = "Upload something"
        step.requires_manual_review = False
        step.source_path = "/path/unknown_file.xyz"
        plan.steps = [step]
        upload_plan = planner.plan(plan)
        assert upload_plan.tasks[0].document_type == DocumentType.RESUME

    def test_executor_upload_no_page(self, executor):
        task = UploadTask(
            task_type=UploadTaskType.UPLOAD,
            field_ref="f1",
            selector="#file",
            document_type=DocumentType.RESUME,
            source=UploadSource(path="/path/f.pdf", document_type=DocumentType.RESUME),
        )
        result = executor.execute_task(None, task)
        assert result.result == UploadTaskResult.FAILED

    def test_validate_file_not_a_file(self, tmp_path, validator):
        d = tmp_path / "adir"
        d.mkdir()
        issues = validator.validate_file(str(d), DocumentType.RESUME)
        assert any("not a file" in i for i in issues)
