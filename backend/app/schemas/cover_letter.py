import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CoverLetterCreate(BaseModel):
    title: str | None = Field(None, max_length=255)
    company_name: str | None = Field(None, max_length=255)
    job_title: str | None = Field(None, max_length=255)
    job_id: str | None = None
    resume_id: str | None = None
    content: str | None = None
    template: str | None = Field(None, max_length=100)
    tone: str | None = Field(None, max_length=50)


class CoverLetterUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    content: str | None = None
    template: str | None = Field(None, max_length=100)
    tone: str | None = Field(None, max_length=50)
    status: str | None = Field(None, pattern=r"^(draft|ready|archived)$")


class CoverLetterResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID | None = None
    resume_id: uuid.UUID | None = None
    title: str | None = None
    company_name: str | None = None
    job_title: str | None = None
    hiring_manager: str | None = None
    template: str | None = None
    tone: str | None = None
    content: str | None = None
    version: int = 1
    status: str = "draft"
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CoverLetterListItem(BaseModel):
    id: uuid.UUID
    title: str | None = None
    company_name: str | None = None
    job_title: str | None = None
    template: str | None = None
    version: int = 1
    status: str = "draft"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CoverLetterGenerateRequest(BaseModel):
    job_id: str
    resume_id: str
    tone: str = Field(default="professional", pattern=r"^(professional|technical|executive|friendly|concise|graduate|career_change)$")
    template: str | None = Field(default="modern", max_length=100)
    hiring_manager: str | None = Field(None, max_length=255)
    company_name: str | None = Field(None, max_length=255)
    additional_notes: str | None = None


class CoverLetterAIAssistRequest(BaseModel):
    section: str
    instruction: str = Field(..., pattern=r"^(rewrite|shorten|expand|professional|technical|grammar|improve|remove_repetition)$")
    context: str | None = None


class CoverLetterVersionCreate(BaseModel):
    content: str
    change_summary: str | None = None


class CoverLetterVersionResponse(BaseModel):
    id: uuid.UUID
    version: int
    content: str
    change_summary: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationPackageRequest(BaseModel):
    resume_id: str
    cover_letter_id: str
    job_id: str
    notes: str | None = None


class ApplicationPackageResponse(BaseModel):
    resume: dict
    cover_letter: dict
    job: dict
    notes: str | None = None


class CoverLetterExportRequest(BaseModel):
    format: str = Field(default="pdf", pattern=r"^(pdf|docx|txt)$")
