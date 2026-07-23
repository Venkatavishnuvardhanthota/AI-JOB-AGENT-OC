from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ExecutionMode(str, Enum):
    DRY_RUN = "dry_run"
    MANUAL_CONFIRMATION = "manual_confirmation"
    AUTOMATIC = "automatic"
    SAFE_RETRY = "safe_retry"


class SubmissionStepType(str, Enum):
    FILL = "fill"
    SELECT = "select"
    CHECK = "check"
    UPLOAD = "upload"
    SKIP = "skip"
    REQUEST_MANUAL = "request_manual"
    SUBMIT = "submit"
    CONFIRM = "confirm"
    VERIFY = "verify"
    VALIDATE = "validate"


class SubmissionStepResult(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"


class StepExecution(BaseModel):
    step_type: SubmissionStepType
    field_ref: str = ""
    selector: str = ""
    result: SubmissionStepResult = SubmissionStepResult.PENDING
    duration_ms: float | None = None
    error: str | None = None
    screenshot_path: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ConfirmationResult(BaseModel):
    confirmed: bool = False
    confirmation_number: str | None = None
    application_id: str | None = None
    confirmation_url: str | None = None
    redirect_url: str | None = None
    duration_ms: float | None = None
    provider_acknowledged: bool = False
    success_page_detected: bool = False
    duplicate_detected: bool = False
    details: str = ""


class ExecutionMetrics(BaseModel):
    total_duration_ms: float | None = None
    field_execution_duration_ms: float | None = None
    upload_duration_ms: float | None = None
    submit_duration_ms: float | None = None
    confirmation_duration_ms: float | None = None
    total_fields: int = 0
    filled_fields: int = 0
    upload_count: int = 0
    skip_count: int = 0
    manual_count: int = 0
    retry_count: int = 0
    failure_count: int = 0
    success_count: int = 0
    screenshots_taken: int = 0


class RetryAttempt(BaseModel):
    attempt_number: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: str = ""
    duration_ms: float | None = None


class SafetyCheck(BaseModel):
    check_name: str = ""
    passed: bool = False
    details: str = ""


class SubmissionReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider_name: str = ""
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN
    status: str = "pending"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: float | None = None
    application_id: str | None = None
    confirmation_number: str | None = None
    confirmation_url: str | None = None
    confirmation_result: ConfirmationResult | None = None
    steps: list[StepExecution] = Field(default_factory=list)
    metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)
    retry_attempts: list[RetryAttempt] = Field(default_factory=list)
    safety_checks: list[SafetyCheck] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    screenshots: list[str] = Field(default_factory=list)
    manual_actions: list[str] = Field(default_factory=list)


class SubmissionState(str, Enum):
    PENDING = "pending"
    VALIDATING = "validating"
    VALIDATED = "validated"
    EXECUTING_FIELDS = "executing_fields"
    EXECUTING_UPLOADS = "executing_uploads"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    SUBMITTING = "submitting"
    CONFIRMING = "confirming"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class SubmissionStatus(BaseModel):
    submission_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    package_id: str = ""
    state: SubmissionState = SubmissionState.PENDING
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN
    provider_name: str = ""
    report: SubmissionReport = Field(default_factory=SubmissionReport)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
