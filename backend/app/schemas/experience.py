import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class ExperienceBase(BaseModel):
    company: str = Field(max_length=255)
    title: str = Field(max_length=255)
    location: str | None = Field(None, max_length=255)
    employment_type: str | None = Field(None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    currently_working: bool | None = None
    responsibilities: list[str] | None = None
    achievements: list[str] | None = None
    technologies_used: list[str] | None = None
    description: str | None = None


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(BaseModel):
    company: str | None = Field(None, max_length=255)
    title: str | None = Field(None, max_length=255)
    location: str | None = Field(None, max_length=255)
    employment_type: str | None = Field(None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    currently_working: bool | None = None
    responsibilities: list[str] | None = None
    achievements: list[str] | None = None
    technologies_used: list[str] | None = None
    description: str | None = None


class ExperienceResponse(ExperienceBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
