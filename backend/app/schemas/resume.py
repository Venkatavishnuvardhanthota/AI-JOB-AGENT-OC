import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

# ── ResumeMaster ──

class ResumeMasterBase(BaseModel):
    name: str
    title: str | None = None
    summary: str | None = None
    template_id: uuid.UUID | None = None
    is_active: bool = True


class ResumeMasterCreate(ResumeMasterBase):
    pass


class ResumeMasterUpdate(BaseModel):
    name: str | None = None
    title: str | None = None
    summary: str | None = None
    template_id: uuid.UUID | None = None
    is_active: bool | None = None


class ResumeMasterResponse(ResumeMasterBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── ResumeVersion ──

class ResumeVersionBase(BaseModel):
    name: str
    notes: str | None = None
    is_active: bool = True


class ResumeVersionCreate(ResumeVersionBase):
    snapshot_data: dict | None = None


class ResumeVersionUpdate(BaseModel):
    name: str | None = None
    notes: str | None = None
    is_active: bool | None = None
    snapshot_data: dict | None = None


class ResumeVersionResponse(ResumeVersionBase):
    id: uuid.UUID
    resume_master_id: uuid.UUID
    version_number: int
    snapshot_data: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateVersionFromSnapshot(BaseModel):
    name: str | None = None
    notes: str | None = None
    profile_fields: list[str] | None = None
    education_ids: list[uuid.UUID] | None = None
    experience_ids: list[uuid.UUID] | None = None
    skill_ids: list[uuid.UUID] | None = None
    project_ids: list[uuid.UUID] | None = None
    certification_ids: list[uuid.UUID] | None = None
    language_ids: list[uuid.UUID] | None = None
    portfolio_item_ids: list[uuid.UUID] | None = None


# ── ResumeTemplate ──

class ResumeTemplateBase(BaseModel):
    name: str
    description: str | None = None
    layout_config: dict | None = None


class ResumeTemplateCreate(ResumeTemplateBase):
    pass


class ResumeTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    layout_config: dict | None = None


class ResumeTemplateResponse(ResumeTemplateBase):
    id: uuid.UUID
    user_id: uuid.UUID | None
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── GeneratedResume ──

class GeneratedResumeResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    resume_version_id: uuid.UUID | None
    format: str
    file_path: str
    file_size: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GenerateResumeRequest(BaseModel):
    resume_version_id: uuid.UUID
    format: str = "pdf"

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        if v.lower() not in ("docx", "pdf"):
            raise ValueError("Format must be 'docx' or 'pdf'")
        return v.lower()


# ── Resume Snapshot for generation (composite data) ──

class ResumeSnapshotData(BaseModel):
    profile: dict | None = None
    education: list[dict] = []
    experience: list[dict] = []
    skills: list[dict] = []
    projects: list[dict] = []
    certifications: list[dict] = []
    languages: list[dict] = []
    portfolio_items: list[dict] = []
    template_config: dict | None = None
