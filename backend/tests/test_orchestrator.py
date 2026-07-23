from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.orchestrator.checkpoint import CheckpointManager
from app.orchestrator.config import OrchestratorConfig
from app.orchestrator.coordinator import (
    ApplicationPackageExecutor,
    ATSDetectionExecutor,
    CoverLetterExecutor,
    FormIntelligenceExecutor,
    JobMatchingExecutor,
    ProfileIntelligenceExecutor,
    ResumeOptimizationExecutor,
    ReviewExecutor,
    TrackingExecutor,
    WorkflowExecutor,
)
from app.orchestrator.dispatcher import ExecutionDispatcher
from app.orchestrator.exceptions import (
    CheckpointError,
    DispatchError,
    ManualInterventionError,
    NonRecoverableError,
    OrchestratorError,
    PipelineExecutionError,
    RecoverableError,
    RecoveryFailedError,
    StageExecutionError,
    ValidationError,
)
from app.orchestrator.metrics import OrchestratorMetricsCollector
from app.orchestrator.pipeline import PipelineEngine
from app.orchestrator.recovery import RecoveryHandler
from app.orchestrator.reporting import OrchestrationReportBuilder
from app.orchestrator.schemas import (
    CheckpointData,
    ExecutionMode,
    OrchestrationContext,
    OrchestrationMetrics,
    OrchestrationReport,
    OrchestratorState,
    PipelineStage,
    RecoveryStrategy,
    StageResult,
    StageStatus,
)
from app.orchestrator.service import OrchestratorService
from app.orchestrator.state import OrchestrationStateManager
from app.orchestrator.validator import OrchestratorValidator


@pytest.fixture
def config() -> OrchestratorConfig:
    return OrchestratorConfig(checkpoint_enabled=True)


@pytest.fixture
def state_manager() -> OrchestrationStateManager:
    return OrchestrationStateManager()


@pytest.fixture
def metrics() -> OrchestratorMetricsCollector:
    return OrchestratorMetricsCollector()


@pytest.fixture
def checkpoint_dir() -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def checkpoint_manager(checkpoint_dir: str) -> CheckpointManager:
    return CheckpointManager(checkpoint_dir=checkpoint_dir)


@pytest.fixture
def recovery_handler(config: OrchestratorConfig, checkpoint_manager: CheckpointManager) -> RecoveryHandler:
    return RecoveryHandler(config, checkpoint_manager)


@pytest.fixture
def context() -> OrchestrationContext:
    return OrchestrationContext(
        execution_mode=ExecutionMode.SINGLE,
        job=MagicMock(id=uuid.uuid4()),
        profile=MagicMock(),
    )


@pytest.fixture
def service(config: OrchestratorConfig) -> OrchestratorService:
    return OrchestratorService(config=config)


@pytest.fixture
def report_builder(metrics: OrchestratorMetricsCollector) -> OrchestrationReportBuilder:
    return OrchestrationReportBuilder(metrics)


# --- Exception Tests ---

class TestExceptions:
    def test_stage_execution_error(self):
        err = StageExecutionError("test_stage", "something broke", recoverable=True)
        assert err.stage == "test_stage"
        assert err.recoverable is True
        assert "test_stage" in str(err)
        assert "something broke" in str(err)

    def test_stage_execution_error_non_recoverable(self):
        err = StageExecutionError("test_stage", "fatal", recoverable=False)
        assert err.recoverable is False

    def test_exception_hierarchy(self):
        assert issubclass(RecoverableError, OrchestratorError)
        assert issubclass(NonRecoverableError, OrchestratorError)
        assert issubclass(ManualInterventionError, OrchestratorError)
        assert issubclass(CheckpointError, OrchestratorError)
        assert issubclass(RecoveryFailedError, OrchestratorError)
        assert issubclass(ValidationError, OrchestratorError)
        assert issubclass(DispatchError, OrchestratorError)


# --- Schema Tests ---

class TestSchemas:
    def test_orchestration_context_defaults(self):
        ctx = OrchestrationContext()
        assert ctx.state == OrchestratorState.IDLE
        assert ctx.execution_mode == ExecutionMode.SINGLE
        assert ctx.orchestration_id is not None
        assert len(ctx.stages) == 0
        assert len(ctx.errors) == 0
        assert len(ctx.warnings) == 0

    def test_orchestration_context_get_stage(self):
        ctx = OrchestrationContext()
        stage = ctx.get_stage(PipelineStage.JOB_MATCHING)
        assert stage.stage == PipelineStage.JOB_MATCHING
        assert stage.status == StageStatus.PENDING
        assert PipelineStage.JOB_MATCHING in ctx.stages

    def test_orchestration_context_set_stage_output(self):
        ctx = OrchestrationContext()
        ctx.get_stage(PipelineStage.JOB_MATCHING).started_at = datetime.utcnow() - timedelta(seconds=5)
        ctx.set_stage_output(PipelineStage.JOB_MATCHING, {"score": 85})
        result = ctx.stages[PipelineStage.JOB_MATCHING]
        assert result.status == StageStatus.COMPLETED
        assert result.output == {"score": 85}
        assert result.duration_ms is not None

    def test_orchestration_context_mark_stage_failed(self):
        ctx = OrchestrationContext()
        ctx.mark_stage_failed(PipelineStage.UPLOAD, "Upload error")
        result = ctx.stages[PipelineStage.UPLOAD]
        assert result.status == StageStatus.FAILED
        assert result.error == "Upload error"

    def test_orchestration_context_mark_stage_skipped(self):
        ctx = OrchestrationContext()
        ctx.mark_stage_skipped(PipelineStage.COVER_LETTER, "No job")
        result = ctx.stages[PipelineStage.COVER_LETTER]
        assert result.status == StageStatus.SKIPPED
        assert "No job" in result.warnings

    def test_stage_result_defaults(self):
        r = StageResult(stage=PipelineStage.JOB_DISCOVERY)
        assert r.status == StageStatus.PENDING
        assert r.retry_count == 0
        assert r.warnings == []

    def test_checkpoint_data_defaults(self):
        ck = CheckpointData(orchestration_id="test-id", stage=PipelineStage.WORKFLOW)
        assert ck.checkpoint_id is not None
        assert ck.version == "1.0"
        assert ck.context_snapshot == {}

    def test_orchestration_metrics_defaults(self):
        m = OrchestrationMetrics()
        assert m.pipeline_duration_ms is None
        assert m.success_count == 0
        assert m.failure_count == 0

    def test_orchestration_report_defaults(self):
        r = OrchestrationReport(
            orchestration_id="id",
            state=OrchestratorState.IDLE,
            execution_mode=ExecutionMode.SINGLE,
        )
        assert r.errors == []
        assert r.warnings == []
        assert r.checkpoints_created == 0
        assert r.retry_history == []


# --- Validator Tests ---

class TestOrchestratorValidator:
    def test_validate_valid_mode(self):
        v = OrchestratorValidator(OrchestratorConfig())
        result = v.validate_mode("single")
        assert result == ExecutionMode.SINGLE

    def test_validate_invalid_mode(self):
        v = OrchestratorValidator(OrchestratorConfig())
        with pytest.raises(ValidationError):
            v.validate_mode("invalid_mode")

    def test_validate_mode_case_sensitive(self):
        v = OrchestratorValidator(OrchestratorConfig())
        with pytest.raises(ValidationError):
            v.validate_mode("SINGLE")

    def test_context_validation_empty(self):
        v = OrchestratorValidator(OrchestratorConfig())
        ctx = OrchestrationContext()
        issues = v.validate_context(ctx)
        assert isinstance(issues, list)


# --- State Manager Tests ---

class TestOrchestrationStateManager:
    def test_set_running(self, state_manager):
        ctx = OrchestrationContext()
        state_manager.set_running(ctx)
        assert ctx.state == OrchestratorState.RUNNING

    def test_set_completed(self, state_manager):
        ctx = OrchestrationContext()
        state_manager.set_running(ctx)
        state_manager.set_completed(ctx)
        assert ctx.state == OrchestratorState.COMPLETED
        assert ctx.completed_at is not None

    def test_set_failed(self, state_manager):
        ctx = OrchestrationContext()
        state_manager.set_failed(ctx, "Critical error")
        assert ctx.state == OrchestratorState.FAILED
        assert "Critical error" in ctx.errors

    def test_set_cancelled(self, state_manager):
        ctx = OrchestrationContext()
        state_manager.set_cancelled(ctx, "User cancelled")
        assert ctx.state == OrchestratorState.CANCELLED
        assert "User cancelled" in ctx.warnings

    def test_is_running(self, state_manager):
        ctx = OrchestrationContext()
        assert not state_manager.is_running(ctx)
        state_manager.set_running(ctx)
        assert state_manager.is_running(ctx)

    def test_is_completed(self, state_manager):
        ctx = OrchestrationContext()
        state_manager.set_completed(ctx)
        assert state_manager.is_completed(ctx)
        ctx2 = OrchestrationContext()
        state_manager.set_failed(ctx2, "err")
        assert state_manager.is_completed(ctx2)

    def test_can_resume(self, state_manager):
        ctx = OrchestrationContext()
        assert not state_manager.can_resume(ctx)
        state_manager.set_failed(ctx, "err")
        assert state_manager.can_resume(ctx)

    def test_set_current_stage(self, state_manager):
        ctx = OrchestrationContext()
        state_manager.set_current_stage(ctx, PipelineStage.JOB_MATCHING)
        assert ctx.current_stage == PipelineStage.JOB_MATCHING


# --- Checkpoint Tests ---

class TestCheckpointManager:
    def test_save_and_load_checkpoint(self, checkpoint_manager):
        ctx = OrchestrationContext()
        ck = checkpoint_manager.create_checkpoint(ctx, PipelineStage.APPLICATION_PACKAGE)
        assert ck.orchestration_id == ctx.orchestration_id
        assert ck.stage == PipelineStage.APPLICATION_PACKAGE

        loaded = checkpoint_manager.load_checkpoint(ck.checkpoint_id)
        assert loaded is not None
        assert loaded.checkpoint_id == ck.checkpoint_id
        assert loaded.stage == ck.stage

    def test_load_nonexistent_checkpoint(self, checkpoint_manager):
        loaded = checkpoint_manager.load_checkpoint("nonexistent")
        assert loaded is None

    def test_restore_context(self, checkpoint_manager):
        ctx = OrchestrationContext(job="test_job")
        ck = checkpoint_manager.create_checkpoint(ctx, PipelineStage.WORKFLOW)
        restored = checkpoint_manager.restore_context(ck)
        assert isinstance(restored, OrchestrationContext)
        assert restored.orchestration_id == ctx.orchestration_id

    def test_list_checkpoints(self, checkpoint_manager):
        ctx = OrchestrationContext()
        ck1 = checkpoint_manager.create_checkpoint(ctx, PipelineStage.APPLICATION_PACKAGE)
        ck2 = checkpoint_manager.create_checkpoint(ctx, PipelineStage.SUBMISSION)
        checkpoints = checkpoint_manager.list_checkpoints(ctx.orchestration_id)
        assert len(checkpoints) == 2

    def test_delete_checkpoint(self, checkpoint_manager):
        ctx = OrchestrationContext()
        ck = checkpoint_manager.create_checkpoint(ctx, PipelineStage.WORKFLOW)
        checkpoint_manager.delete_checkpoint(ck.checkpoint_id)
        loaded = checkpoint_manager.load_checkpoint(ck.checkpoint_id)
        assert loaded is None

    def test_clear_all(self, checkpoint_manager):
        ctx = OrchestrationContext()
        checkpoint_manager.create_checkpoint(ctx, PipelineStage.JOB_MATCHING)
        checkpoint_manager.create_checkpoint(ctx, PipelineStage.REVIEW)
        checkpoint_manager.clear_all(ctx.orchestration_id)
        assert len(checkpoint_manager.list_checkpoints(ctx.orchestration_id)) == 0


# --- Recovery Tests ---

class TestRecoveryHandler:
    def test_determine_strategy_retry(self, config, checkpoint_manager):
        handler = RecoveryHandler(config, checkpoint_manager)
        ctx = OrchestrationContext()
        strategy = handler.determine_strategy(ctx, PipelineStage.UPLOAD, "timeout error", 1)
        assert strategy == RecoveryStrategy.RETRY_STAGE

    def test_determine_strategy_manual_intervention(self, config, checkpoint_manager):
        handler = RecoveryHandler(config, checkpoint_manager)
        ctx = OrchestrationContext()
        strategy = handler.determine_strategy(ctx, PipelineStage.UPLOAD, "invalid request", 1)
        assert strategy == RecoveryStrategy.MANUAL_INTERVENTION

    def test_determine_strategy_abort_after_max_retries(self, config, checkpoint_manager):
        config.max_retries_per_stage = 2
        handler = RecoveryHandler(config, checkpoint_manager)
        ctx = OrchestrationContext()
        strategy = handler.determine_strategy(ctx, PipelineStage.SUBMISSION, "error", 3)
        assert strategy == RecoveryStrategy.MANUAL_INTERVENTION

    def test_execute_retry_strategy(self, config, checkpoint_manager):
        handler = RecoveryHandler(config, checkpoint_manager)
        ctx = OrchestrationContext()
        result = handler.execute_strategy(
            ctx, PipelineStage.UPLOAD, RecoveryStrategy.RETRY_STAGE, "timeout", 1
        )
        stage = result.get_stage(PipelineStage.UPLOAD)
        assert stage.status == StageStatus.PENDING
        assert stage.retry_count == 1

    def test_execute_manual_intervention(self, config, checkpoint_manager):
        handler = RecoveryHandler(config, checkpoint_manager)
        ctx = OrchestrationContext()
        result = handler.execute_strategy(
            ctx, PipelineStage.SUBMISSION, RecoveryStrategy.MANUAL_INTERVENTION, "error", 1
        )
        assert any("Manual intervention required" in w for w in result.warnings)

    def test_is_retryable_true(self, config, checkpoint_manager):
        handler = RecoveryHandler(config, checkpoint_manager)
        assert handler._is_retryable("timeout error")
        assert handler._is_retryable("connection refused")

    def test_is_retryable_false(self, config, checkpoint_manager):
        handler = RecoveryHandler(config, checkpoint_manager)
        assert not handler._is_retryable("invalid request")
        assert not handler._is_retryable("unauthorized access")


# --- Dispatcher Tests ---

class TestExecutionDispatcher:
    def test_dispatch_single(self):
        d = ExecutionDispatcher()
        ctx = OrchestrationContext(execution_mode=ExecutionMode.SINGLE)
        result = d.dispatch(ctx)
        assert result.execution_mode == ExecutionMode.SINGLE

    def test_dispatch_dry_run(self):
        d = ExecutionDispatcher()
        ctx = OrchestrationContext(execution_mode=ExecutionMode.DRY_RUN)
        result = d.dispatch(ctx)
        assert any("Dry run" in w for w in result.warnings)

    def test_dispatch_manual(self):
        d = ExecutionDispatcher()
        ctx = OrchestrationContext(execution_mode=ExecutionMode.MANUAL)
        result = d.dispatch(ctx)
        assert result.state == OrchestratorState.PAUSED

    def test_dispatch_unknown_value(self):
        dispatcher = ExecutionDispatcher()
        valid_modes = [m.value for m in ExecutionMode]
        assert "single" in valid_modes
        assert "batch" in valid_modes
        assert "dry_run" in valid_modes


# --- Metrics Tests ---

class TestOrchestratorMetricsCollector:
    def test_record_stage(self, metrics):
        ctx = OrchestrationContext()
        metrics.record_stage_start(PipelineStage.JOB_MATCHING, ctx)
        import time
        time.sleep(0.01)
        metrics.record_stage_end(PipelineStage.JOB_MATCHING, ctx)
        result = ctx.get_stage(PipelineStage.JOB_MATCHING)
        assert result.duration_ms is not None
        assert result.duration_ms > 0

    def test_get_metrics(self, metrics):
        ctx = OrchestrationContext()
        ctx.started_at = datetime.utcnow() - timedelta(seconds=10)
        ctx.completed_at = datetime.utcnow()
        ctx.set_stage_output(PipelineStage.JOB_MATCHING, "ok")
        ctx.set_stage_output(PipelineStage.APPLICATION_PACKAGE, "ok")
        ctx.mark_stage_failed(PipelineStage.UPLOAD, "error")
        ctx.mark_stage_skipped(PipelineStage.COVER_LETTER, "no job")

        collected = metrics.get_metrics(ctx)
        assert collected.success_count == 2
        assert collected.failure_count == 1
        assert collected.skip_count == 1
        assert collected.pipeline_duration_ms is not None


# --- Reporting Tests ---

class TestOrchestrationReportBuilder:
    def test_build_basic_report(self, metrics, report_builder):
        ctx = OrchestrationContext()
        ctx.started_at = datetime.utcnow() - timedelta(seconds=5)
        ctx.completed_at = datetime.utcnow()
        ctx.state = OrchestratorState.COMPLETED

        report = report_builder.build(ctx)
        assert report.orchestration_id == ctx.orchestration_id
        assert report.state == OrchestratorState.COMPLETED
        assert report.total_duration_ms is not None

    def test_build_with_stages(self, metrics, report_builder):
        ctx = OrchestrationContext()
        ctx.set_stage_output(PipelineStage.JOB_MATCHING, {"score": 85})
        report = report_builder.build(ctx)
        assert PipelineStage.JOB_MATCHING.value in report.stages

    def test_build_with_errors(self, metrics, report_builder):
        ctx = OrchestrationContext()
        ctx.errors.append("Something went wrong")
        report = report_builder.build(ctx)
        assert "Something went wrong" in report.errors


# --- Pipeline Tests ---

class TestPipelineEngine:
    def test_dry_run_skips_stages(self, config, checkpoint_manager, recovery_handler, metrics, state_manager):
        engine = PipelineEngine(config, checkpoint_manager, recovery_handler, metrics, state_manager, [])
        ctx = OrchestrationContext(execution_mode=ExecutionMode.DRY_RUN)
        result = engine.run(ctx)
        assert result.state == OrchestratorState.COMPLETED

    @patch("app.orchestrator.coordinator.JobMatchingExecutor")
    def test_successful_pipeline(self, mock_exec, config, checkpoint_manager, recovery_handler, metrics, state_manager):
        mock_exec.stage.return_value = PipelineStage.JOB_MATCHING
        mock_exec.is_skippable.return_value = False
        mock_exec.should_skip.return_value = False

        def _execute(ctx):
            ctx.set_stage_output(PipelineStage.JOB_MATCHING, {"match": True})
            return ctx
        mock_exec.execute.side_effect = _execute

        engine = PipelineEngine(config, checkpoint_manager, recovery_handler, metrics, state_manager, [mock_exec])
        ctx = OrchestrationContext(execution_mode=ExecutionMode.SINGLE)
        result = engine.run(ctx)
        assert result.state == OrchestratorState.COMPLETED

    def test_empty_executors(self, config, checkpoint_manager, recovery_handler, metrics, state_manager):
        engine = PipelineEngine(config, checkpoint_manager, recovery_handler, metrics, state_manager, [])
        ctx = OrchestrationContext(execution_mode=ExecutionMode.SINGLE)
        result = engine.run(ctx)
        assert result.state == OrchestratorState.COMPLETED


# --- Stage Executor Tests ---

class TestStageExecutors:
    def test_profile_intelligence_skip_no_user(self):
        ex = ProfileIntelligenceExecutor()
        assert ex.stage() == PipelineStage.PROFILE_INTELLIGENCE
        assert ex.is_skippable()
        ctx = OrchestrationContext()
        assert ex.should_skip(ctx) is True

    def test_job_matching_skip_no_profile(self):
        ex = JobMatchingExecutor()
        ctx = OrchestrationContext()
        assert ex.should_skip(ctx) is True

    def test_job_matching_skip_no_job(self):
        ex = JobMatchingExecutor()
        ctx = OrchestrationContext(profile=MagicMock())
        assert ex.should_skip(ctx) is True

    def test_job_matching_not_skipped(self):
        ex = JobMatchingExecutor()
        ctx = OrchestrationContext(profile=MagicMock(), job=MagicMock(id=1))
        assert ex.should_skip(ctx) is False

    def test_ats_detection_should_skip(self):
        ex = ATSDetectionExecutor()
        ctx = OrchestrationContext(ats_result="already_detected")
        assert ex.should_skip(ctx) is True

    def test_ats_detection_not_skipped(self):
        ex = ATSDetectionExecutor()
        ctx = OrchestrationContext()
        assert ex.should_skip(ctx) is False

    def test_form_intelligence_skip(self):
        ex = FormIntelligenceExecutor()
        ctx = OrchestrationContext(form_analysis="done")
        assert ex.should_skip(ctx) is True

    def test_workflow_executor_stage(self):
        ex = WorkflowExecutor()
        assert ex.stage() == PipelineStage.WORKFLOW
        assert ex.is_skippable()

    def test_review_executor_skip_no_package(self):
        ex = ReviewExecutor()
        ctx = OrchestrationContext()
        assert ex.should_skip(ctx) is True

    def test_application_package_executor_stage(self):
        ex = ApplicationPackageExecutor()
        assert ex.stage() == PipelineStage.APPLICATION_PACKAGE

    def test_resume_optimization_skip_no_profile(self):
        ex = ResumeOptimizationExecutor()
        ctx = OrchestrationContext()
        assert ex.should_skip(ctx) is True

    def test_cover_letter_skip_no_profile(self):
        ex = CoverLetterExecutor()
        ctx = OrchestrationContext()
        assert ex.should_skip(ctx) is True

    def test_tracking_executor_not_skippable(self):
        ex = TrackingExecutor()
        assert ex.is_skippable() is False


# --- Service Tests ---

class TestOrchestratorService:
    def test_validate_mode_valid(self, service):
        service.validate_mode("single")

    def test_validate_mode_invalid(self, service):
        with pytest.raises(ValidationError):
            service.validate_mode("invalid")

    def test_get_available_stages(self, service):
        stages = service.get_available_stages()
        assert len(stages) > 0
        assert "job_matching" in stages
        assert "submission" in stages

    def test_dry_run(self, service):
        report = service.run(execution_mode="dry_run")
        assert report.state == OrchestratorState.COMPLETED
        assert any("Dry run" in w for w in report.warnings)

    def test_manual_mode_pauses(self, service):
        report = service.run(execution_mode="manual")
        assert report.execution_mode == ExecutionMode.MANUAL

    @patch("app.orchestrator.service.OrchestratorService.run")
    def test_cancel(self, mock_run, service):
        service.cancel("test-id", "Cancelled by user")

    def test_list_checkpoints_empty(self, service):
        result = service.list_checkpoints("nonexistent")
        assert result == []

    def test_clear_checkpoints(self, service):
        service.clear_checkpoints("test-id")

    def test_resume_nonexistent_checkpoint(self, service):
        with pytest.raises(CheckpointError, match="not found"):
            service.resume("nonexistent")


# --- Integration-style Tests ---

class TestOrchestratorIntegration:
    def test_context_serialization_roundtrip(self):
        ctx = OrchestrationContext(
            execution_mode=ExecutionMode.SINGLE,
            job={"title": "Software Engineer"},
        )
        data = ctx.model_dump()
        restored = OrchestrationContext(**data)
        assert restored.orchestration_id == ctx.orchestration_id
        assert restored.execution_mode == ExecutionMode.SINGLE
        assert restored.job == {"title": "Software Engineer"}

    def test_full_pipeline_with_mocks(self, config, checkpoint_manager, recovery_handler, metrics, state_manager):
        executors = []
        for stage in PipelineStage:
            mock = MagicMock()
            mock.stage.return_value = stage
            mock.is_skippable.return_value = True
            mock.should_skip.return_value = True
            mock.execute.side_effect = lambda ctx, s=stage: ctx
            executors.append(mock)

        engine = PipelineEngine(config, checkpoint_manager, recovery_handler, metrics, state_manager, executors)
        ctx = OrchestrationContext(execution_mode=ExecutionMode.SINGLE)
        result = engine.run(ctx)
        assert result.state == OrchestratorState.COMPLETED

    def test_pipeline_recovery_on_failure(self, config, checkpoint_manager, recovery_handler, metrics, state_manager):
        fast_config = OrchestratorConfig(
            max_retries_per_stage=1,
            retry_delay_seconds=0.01,
            backoff_multiplier=1.0,
        )
        fast_recovery = RecoveryHandler(fast_config, checkpoint_manager)
        mock_exec = MagicMock()
        mock_exec.stage.return_value = PipelineStage.JOB_MATCHING
        mock_exec.is_skippable.return_value = False
        mock_exec.should_skip.return_value = False

        def _execute(ctx):
            raise StageExecutionError("job_matching", "temporary error", recoverable=True)
        mock_exec.execute.side_effect = _execute

        engine = PipelineEngine(fast_config, checkpoint_manager, fast_recovery, metrics, state_manager, [mock_exec])
        ctx = OrchestrationContext(execution_mode=ExecutionMode.SINGLE)
        result = engine.run(ctx)
        assert result.state == OrchestratorState.PAUSED
        assert any("manual intervention" in w.lower() for w in result.warnings)

    def test_metrics_tracking(self, metrics):
        ctx = OrchestrationContext()
        ctx.started_at = datetime.utcnow() - timedelta(seconds=5)
        ctx.completed_at = datetime.utcnow()
        ctx.set_stage_output(PipelineStage.JOB_DISCOVERY, {"count": 10})
        ctx.mark_stage_failed(PipelineStage.UPLOAD, "disk full")
        ctx.mark_stage_skipped(PipelineStage.COVER_LETTER, "no job")

        m = metrics.get_metrics(ctx)
        assert m.success_count == 1
        assert m.failure_count == 1
        assert m.skip_count == 1
        assert m.pipeline_duration_ms is not None

    def test_checkpoint_with_metadata(self, checkpoint_manager):
        ctx = OrchestrationContext()
        ctx.metadata["custom"] = "value"
        ck = checkpoint_manager.create_checkpoint(ctx, PipelineStage.REVIEW)
        loaded = checkpoint_manager.load_checkpoint(ck.checkpoint_id)
        restored = checkpoint_manager.restore_context(loaded)
        assert restored.orchestration_id == ctx.orchestration_id
        assert restored.metadata.get("custom") == "value"

    def test_multiple_checkpoints_same_orchestration(self, checkpoint_manager):
        ctx = OrchestrationContext()
        ck1 = checkpoint_manager.create_checkpoint(ctx, PipelineStage.JOB_DISCOVERY)
        ck2 = checkpoint_manager.create_checkpoint(ctx, PipelineStage.JOB_MATCHING)
        ck3 = checkpoint_manager.create_checkpoint(ctx, PipelineStage.APPLICATION_PACKAGE)
        checkpoints = checkpoint_manager.list_checkpoints(ctx.orchestration_id)
        assert len(checkpoints) == 3
        assert checkpoints[0].stage == PipelineStage.JOB_DISCOVERY
        assert checkpoints[-1].stage == PipelineStage.APPLICATION_PACKAGE

    def test_dispatcher_batch_mode(self):
        d = ExecutionDispatcher()
        ctx = OrchestrationContext(execution_mode=ExecutionMode.BATCH)
        result = d.dispatch(ctx)
        assert result.metadata.get("batch_mode") is True

    def test_dispatcher_scheduled_mode(self):
        d = ExecutionDispatcher()
        ctx = OrchestrationContext(execution_mode=ExecutionMode.SCHEDULED)
        result = d.dispatch(ctx)
        assert result.metadata.get("scheduled") is True

    def test_report_with_retry_history(self, metrics, report_builder):
        ctx = OrchestrationContext()
        ctx.state = OrchestratorState.FAILED
        ctx._retry_history = []
        from app.orchestrator.schemas import RetryHistoryEntry
        ctx._retry_history.append(
            RetryHistoryEntry(
                stage=PipelineStage.UPLOAD,
                attempt=1,
                error="timeout",
                strategy=RecoveryStrategy.RETRY_STAGE,
            )
        )
        report = report_builder.build(ctx)
        assert len(report.retry_history) == 1
        assert report.retry_history[0].stage == PipelineStage.UPLOAD
