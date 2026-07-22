import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    name: str = Field(max_length=255)
    description: str | None = None
    technologies: list[str] | None = None
    github_url: str | None = None
    demo_url: str | None = None
    live_url: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    technologies: list[str] | None = None
    github_url: str | None = None
    demo_url: str | None = None
    live_url: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectResponse(ProjectBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
