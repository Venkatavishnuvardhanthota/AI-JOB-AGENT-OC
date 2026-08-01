import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.validators import validate_url


class ProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    technologies: list[str] | None = None
    github_url: str | None = None
    demo_url: str | None = None
    live_url: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("github_url", "demo_url", "live_url")
    @classmethod
    def _validate_urls(cls, v: str | None) -> str | None:
        return validate_url(v)

    @model_validator(mode="after")
    def _validate_dates(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("End date must be on or after the start date")
        return self


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    technologies: list[str] | None = None
    github_url: str | None = None
    demo_url: str | None = None
    live_url: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    @field_validator("github_url", "demo_url", "live_url")
    @classmethod
    def _validate_urls(cls, v: str | None) -> str | None:
        return validate_url(v)

    @model_validator(mode="after")
    def _validate_dates(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("End date must be on or after the start date")
        return self


class ProjectResponse(ProjectBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
