import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator


class ExperienceBase(BaseModel):
    company: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    location: str | None = Field(None, max_length=255)
    employment_type: str | None = Field(None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    currently_working: bool | None = None
    responsibilities: list[str] | None = None
    achievements: list[str] | None = None
    technologies_used: list[str] | None = None
    description: str | None = None

    @model_validator(mode="after")
    def _validate_dates(self):
        if self.currently_working:
            if self.end_date is not None:
                raise ValueError("End date must be empty when this is your current job")
        elif (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("End date must be on or after the start date")
        return self


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(BaseModel):
    company: str | None = Field(None, min_length=1, max_length=255)
    title: str | None = Field(None, min_length=1, max_length=255)
    location: str | None = Field(None, max_length=255)
    employment_type: str | None = Field(None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    currently_working: bool | None = None
    responsibilities: list[str] | None = None
    achievements: list[str] | None = None
    technologies_used: list[str] | None = None
    description: str | None = None

    @model_validator(mode="after")
    def _validate_dates(self):
        if self.currently_working:
            if self.end_date is not None:
                raise ValueError("End date must be empty when this is your current job")
        elif (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("End date must be on or after the start date")
        return self


class ExperienceResponse(ExperienceBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
