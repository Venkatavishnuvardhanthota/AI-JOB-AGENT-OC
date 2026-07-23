from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PipelineStage(str, Enum):
    PROFILE_INTELLIGENCE = "profile_intelligence"
    JOB_DISCOVERY = "job_discovery"
    JOB_MATCHING = "job_matching"
    APPLICATION_INTELLIGENCE = "application_intelligence"
    RESUME_OPTIMIZATION = "resume_optimization"
    COVER_LETTER = "cover_letter"
    APPLICATION_PACKAGE = "application_package"
    REVIEW = "review"
    WORKFLOW = "workflow"
    ATS_DETECTION = "ats_detection"
    FORM_INTELLIGENCE = "form_intelligence"
    UPLOAD = "upload"
    SUBMISSION = "submission"
    TRACKING = "tracking"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class ExecutionMode(str, Enum):
    SINGLE = "single"
    BATCH = "batch"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    DRY_RUN = "dry_run"


class OrchestratorState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RecoveryStrategy(str, Enum):
    RETRY_STAGE = "retry_stage"
    RESTART_STAGE = "restart_stage"
    ROLLBACK_WORKFLOW = "rollback_workflow"
    MANUAL_INTERVENTION = "manual_intervention"
    ABORT = "abort"


class StageResult(BaseModel):
    stage: PipelineStage
    status: StageStatus = StageStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None
    output: Any = None
    error: str | None = None
    warnings: list[str] = Field(default_factory=list)
    checkpoint_id: str | None = None
    retry_count: int = 0


class CheckpointData(BaseModel):
    checkpoint_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    orchestration_id: str
    stage: PipelineStage
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context_snapshot: dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0"


class OrchestrationContext(BaseModel):
    orchestration_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    execution_mode: ExecutionMode = ExecutionMode.SINGLE
    state: OrchestratorState = OrchestratorState.IDLE
    current_stage: PipelineStage | None = None
    stages: dict[PipelineStage, StageResult] = Field(default_factory=dict)

    workflow_id: str | None = None
    tracking_id: str | None = None
    review_id: str | None = None

    job: Any = None
    profile: Any = None
    user_id: Any = None
    matched_jobs: list[Any] = Field(default_factory=list)
    match_result: Any = None
    application_intelligence: Any = None
    optimized_resume: Any = None
    generated_cover_letter: Any = None
    application_package: Any = None
    review_record: Any = None
    ats_result: Any = None
    form_analysis: Any = None
    execution_plan: Any = None
    upload_plan: Any = None
    upload_results: list[Any] = Field(default_factory=list)
    submission_report: Any = None
    tracking_record: Any = None

    started_at: datetime | None = None
    completed_at: datetime | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    checkpoint: CheckpointData | None = None

    def get_stage(self, stage: PipelineStage) -> StageResult:
        if stage not in self.stages:
            self.stages[stage] = StageResult(stage=stage)
        return self.stages[stage]

    def set_stage_output(self, stage: PipelineStage, output: Any) -> None:
        result = self.get_stage(stage)
        result.output = output
        result.status = StageStatus.COMPLETED
        result.completed_at = datetime.utcnow()
        if result.started_at:
            result.duration_ms = (result.completed_at - result.started_at).total_seconds() * 1000

    def mark_stage_failed(self, stage: PipelineStage, error: str) -> None:
        result = self.get_stage(stage)
        result.status = StageStatus.FAILED
        result.error = error
        result.completed_at = datetime.utcnow()

    def mark_stage_skipped(self, stage: PipelineStage, reason: str = "") -> None:
        result = self.get_stage(stage)
        result.status = StageStatus.SKIPPED
        result.completed_at = datetime.utcnow()
        if reason:
            result.warnings.append(reason)


class OrchestrationMetrics(BaseModel):
    pipeline_duration_ms: float | None = None
    stage_durations: dict[str, float] = Field(default_factory=dict)
    success_count: int = 0
    failure_count: int = 0
    skip_count: int = 0
    retry_count: int = 0
    checkpoint_count: int = 0


class RetryHistoryEntry(BaseModel):
    stage: PipelineStage
    attempt: int
    error: str
    strategy: RecoveryStrategy
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OrchestrationReport(BaseModel):
    orchestration_id: str
    state: OrchestratorState
    execution_mode: ExecutionMode
    stages: dict[str, StageResult] = Field(default_factory=dict)
    metrics: OrchestrationMetrics = Field(default_factory=OrchestrationMetrics)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_duration_ms: float | None = None
    checkpoints_created: int = 0
    retry_history: list[RetryHistoryEntry] = Field(default_factory=list)
