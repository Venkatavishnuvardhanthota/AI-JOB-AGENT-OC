import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FormFieldValue(BaseModel):
    selector: str = Field(..., min_length=1)
    value: str
    field_type: str = Field(default="text", pattern=r"^(text|textarea|checkbox|dropdown|radio|file)$")
    required: bool = False


class ApplicationFormData(BaseModel):
    url: str = Field(..., min_length=1)
    fields: list[FormFieldValue] = []
    resume_file_path: str | None = None
    cover_letter_file_path: str | None = None
    certificate_file_paths: list[str] = []


class AutomationStepResult(BaseModel):
    step_name: str
    success: bool
    duration_ms: int = 0
    error: str | None = None
    screenshot_path: str | None = None


class BrowserAutomationResult(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_posting_id: uuid.UUID | None = None
    url: str
    site_name: str | None = None
    status: str = Field(default="pending", pattern=r"^(pending|running|success|failed|partial)$")
    steps: list[AutomationStepResult] = []
    error: str | None = None
    screenshot_paths: list[str] = []
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AutomationRunRequest(BaseModel):
    url: str = Field(..., min_length=1)
    job_posting_id: uuid.UUID | None = None
    site_name: str | None = None
    fields: list[FormFieldValue] = []
    resume_file_path: str | None = None
    cover_letter_file_path: str | None = None
    certificate_file_paths: list[str] = []


class AutomationRunResponse(BaseModel):
    id: uuid.UUID
    status: str
    message: str


class AutomationLogListItem(BaseModel):
    id: uuid.UUID
    url: str
    site_name: str | None = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SiteConfigResponse(BaseModel):
    site_name: str
    consent_status: str
    url_pattern: str
    field_selectors: list[str] | None = None
    supports_file_upload: bool = False
