from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    RESUME = "resume"
    COVER_LETTER = "cover_letter"
    PORTFOLIO = "portfolio"
    TRANSCRIPT = "transcript"
    CERTIFICATE = "certificate"
    WORK_SAMPLE = "work_sample"
    SUPPORTING_DOCUMENT = "supporting_document"
    CUSTOM = "custom"


class UploadFieldInfo(BaseModel):
    selector: str = ""
    accepted_mime_types: list[str] = Field(default_factory=list)
    accepted_extensions: list[str] = Field(default_factory=list)
    max_size_mb: float | None = None
    min_size_bytes: int | None = None
    multiple: bool = False
    required: bool = False
    replace_existing: bool = False
    remove_existing: bool = False
    supports_drag_and_drop: bool = False
    native_file_input: bool = True
    provider_limitations: list[str] = Field(default_factory=list)


class UploadSource(BaseModel):
    path: str
    document_type: DocumentType
    original_filename: str | None = None
    size_bytes: int | None = None
    mime_type: str | None = None


class UploadTaskType(str, Enum):
    UPLOAD = "upload"
    SKIP = "skip"
    MANUAL = "manual"


class RetryPolicy(BaseModel):
    max_attempts: int = 3
    delay_seconds: float = 2.0
    backoff_multiplier: float = 2.0
    max_delay_seconds: float = 60.0
    retryable_errors: list[str] = Field(default_factory=lambda: [
        "UPLOAD_TIMEOUT_ERROR",
        "UPLOAD_EXECUTION_ERROR",
    ])


class VerificationPolicy(BaseModel):
    verify_after_upload: bool = True
    verify_timeout_ms: float = 10000.0
    check_filename_displayed: bool = True
    check_completion_indicator: bool = True
    check_provider_confirmation: bool = False
    check_element_state: bool = True
    check_error_messages: bool = True


class UploadTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_type: UploadTaskType = UploadTaskType.UPLOAD
    field_ref: str
    selector: str = ""
    source: UploadSource | None = None
    document_type: DocumentType
    field_info: UploadFieldInfo = Field(default_factory=UploadFieldInfo)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    verification_policy: VerificationPolicy = Field(default_factory=VerificationPolicy)
    reason: str = ""
    requires_manual_review: bool = False


class UploadTaskResult(str, Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    SUCCESS = "success"
    SKIPPED = "skipped"
    FAILED = "failed"
    TIMEOUT = "timeout"
    REJECTED = "rejected"
    VERIFICATION_FAILED = "verification_failed"
    MANUAL_REQUIRED = "manual_required"


class UploadAttempt(BaseModel):
    attempt_number: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    result: UploadTaskResult = UploadTaskResult.PENDING
    error_message: str | None = None
    duration_ms: float | None = None


class UploadPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tasks: list[UploadTask] = Field(default_factory=list)
    execution_plan_ref: str | None = None
    total_tasks: int = 0
    upload_tasks: int = 0
    skip_tasks: int = 0
    manual_tasks: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UploadResult(BaseModel):
    task_id: str
    field_ref: str
    result: UploadTaskResult
    attempts: list[UploadAttempt] = Field(default_factory=list)
    final_error: str | None = None
    verified: bool = False
    verification_details: str | None = None
    duration_ms: float | None = None


class UploadSummary(BaseModel):
    plan_id: str = ""
    total: int = 0
    success: int = 0
    skipped: int = 0
    failed: int = 0
    timed_out: int = 0
    rejected: int = 0
    verification_failed: int = 0
    manual_required: int = 0
    total_duration_ms: float | None = None


class ProviderCapabilities(BaseModel):
    provider_name: str = ""
    supports_single_file: bool = True
    supports_multiple_files: bool = False
    supports_drag_and_drop: bool = False
    supports_replace: bool = False
    supports_remove: bool = False
    accepted_types: list[str] = Field(default_factory=list)
    max_file_size_mb: float | None = None
    min_file_size_bytes: int | None = None
    limitations: list[str] = Field(default_factory=list)


class VerificationResult(BaseModel):
    verified: bool = False
    filename_displayed: bool = False
    completion_indicator_found: bool = False
    provider_confirmation_received: bool = False
    element_state_valid: bool = False
    error_messages_found: list[str] = Field(default_factory=list)
    details: str = ""


class NormalizedDocument(BaseModel):
    document_type: DocumentType
    label: str = ""
    extensions: list[str] = Field(default_factory=list)
    mime_types: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class UploadRequest(BaseModel):
    document_type: DocumentType
    file_path: str
    original_filename: str | None = None
    field_ref: str | None = None
    selector: str | None = None
    multiple: bool = False
    replace_existing: bool = False
    remove_existing: bool = False
