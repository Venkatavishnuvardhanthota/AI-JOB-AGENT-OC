import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CoverLetterGenerateRequest(BaseModel):
    job_title: str = Field(..., min_length=1, max_length=500)
    company_name: str = Field(..., min_length=1, max_length=500)
    hiring_manager_name: str | None = None
    job_description: str = Field(..., min_length=10)
    user_full_name: str | None = None
    current_role: str | None = None
    years_experience: int | None = Field(default=None, ge=0)
    field: str | None = None
    key_skills: str | None = None
    relevant_experience: str | None = None
    reason_for_interest: str | None = None
    resume_snapshot: dict | None = None
    resume_version_id: uuid.UUID | None = None
    tone: str | None = Field(default="professional", pattern=r"^(professional|enthusiastic|formal|casual)$")
    length: str | None = Field(default="medium", pattern=r"^(short|medium|long)$")
    include_company_research: bool = True
    export_format: str | None = Field(default=None, pattern=r"^(pdf|docx)$")


class CoverLetterResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_posting_id: uuid.UUID | None = None
    company_name: str
    job_title: str
    hiring_manager_name: str | None = None
    content: str
    version: int
    file_path: str | None = None
    file_format: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CoverLetterListItem(BaseModel):
    id: uuid.UUID
    company_name: str
    job_title: str
    version: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CoverLetterExportRequest(BaseModel):
    format: str = Field(default="pdf", pattern=r"^(pdf|docx)$")
