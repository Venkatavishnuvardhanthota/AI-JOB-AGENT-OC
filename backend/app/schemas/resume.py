import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ResumeSectionCreate(BaseModel):
    section_type: str = Field(min_length=1, max_length=50)
    title: str | None = Field(None, max_length=255)
    content: dict | None = None
    sort_order: int = 0
    visible: bool = True


class ResumeSectionUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    content: dict | None = None
    sort_order: int | None = None
    visible: bool | None = None


class ResumeSectionResponse(BaseModel):
    id: uuid.UUID
    section_type: str
    title: str | None
    content: dict | None
    sort_order: int
    visible: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeSectionReorderItem(BaseModel):
    section_id: uuid.UUID
    sort_order: int


class ResumeSectionReorder(BaseModel):
    order: list[ResumeSectionReorderItem]


class ResumeCreate(BaseModel):
    title: str | None = Field(None, max_length=255)
    description: str | None = None
    template: str | None = Field(None, max_length=100)
    resume_type: str | None = Field(None, max_length=50)
    change_summary: str | None = None
    sections: list[ResumeSectionCreate] = []


class ResumeUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    description: str | None = None
    template: str | None = Field(None, max_length=100)
    resume_type: str | None = Field(None, max_length=50)
    status: str | None = Field(None, pattern=r"^(draft|active|archived)$")
    change_summary: str | None = None


class ResumeExportData(BaseModel):
    version: int
    title: str | None
    description: str | None
    template: str | None
    resume_type: str | None
    status: str
    source: str
    change_summary: str | None
    sections: list[ResumeSectionResponse]
    created_at: datetime
    updated_at: datetime


class ResumeImportData(BaseModel):
    title: str | None = Field(None, max_length=255)
    description: str | None = None
    template: str | None = Field(None, max_length=100)
    resume_type: str | None = Field(None, max_length=50)
    status: str = "draft"
    change_summary: str | None = None
    sections: list[ResumeSectionCreate] = []


class ResumeResponse(BaseModel):
    id: uuid.UUID
    version: int
    title: str | None
    description: str | None
    template: str | None
    status: str
    source: str
    origin: str | None = None
    resume_type: str | None
    is_default: bool
    change_summary: str | None
    archived: bool
    sections: list[ResumeSectionResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ResumeListResponse(BaseModel):
    id: uuid.UUID
    version: int
    title: str | None
    template: str | None
    status: str
    source: str
    origin: str | None = None
    is_default: bool
    archived: bool
    section_count: int = 0
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class ResumeGenerateRequest(BaseModel):
    title: str | None = None
    sections: list[str] | None = None
    enhance_with_ai: bool = False


class ResumeOptimizeRequest(BaseModel):
    job_id: str
    target_role: str | None = None
    enhance_with_ai: bool = True


class ResumeUploadResponse(BaseModel):
    filename: str
    file_size: int
    sections: list[ResumeSectionCreate]
    confidence: float
    needs_review: list[str]


class ResumePreviewResponse(BaseModel):
    html: str


class TemplateResponse(BaseModel):
    id: str
    name: str


# ── ATS / Health / Analysis ──


class AtsCategory(BaseModel):
    name: str
    score: float
    reason: str
    suggestion: str
    missing: list[str] = []


class AtsAnalysisResponse(BaseModel):
    overall: float
    categories: list[AtsCategory]
    strengths: list[str]
    improvements: list[str]


class ResumeHealthResponse(BaseModel):
    overall: float
    strengths: list[dict]
    improvements: list[dict]
    recommendations: list[str]


class ResumeAnalyzeRequest(BaseModel):
    job_id: str
    target_role: str | None = None


class ResumeAnalyzeResponse(BaseModel):
    ats: AtsAnalysisResponse
    health: ResumeHealthResponse
