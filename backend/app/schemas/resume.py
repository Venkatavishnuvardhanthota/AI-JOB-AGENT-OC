import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ResumeCreate(BaseModel):
    job_id: uuid.UUID | None = None
    template: str = Field(default="modern", max_length=100)
    title: str | None = Field(None, max_length=255)


class ResumeResponse(BaseModel):
    id: uuid.UUID
    version: int
    title: str | None
    template: str | None
    content: dict | None
    archived: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeListResponse(BaseModel):
    id: uuid.UUID
    title: str | None
    template: str | None
    version: int
    archived: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ResumePreviewResponse(BaseModel):
    html: str


class ResumeCompareResponse(BaseModel):
    left_version: int
    right_version: int
    changes: list[dict]


class TemplateResponse(BaseModel):
    id: str
    name: str
