import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator


class EducationBase(BaseModel):
    institution: str = Field(min_length=1, max_length=255)
    degree: str = Field(min_length=1, max_length=255)
    field_of_study: str | None = Field(None, max_length=255)
    location: str | None = Field(None, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    currently_studying: bool | None = None
    cgpa: str | None = Field(None, max_length=20)

    @model_validator(mode="after")
    def _validate_dates(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("End date must be on or after the start date")
        return self


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    institution: str | None = Field(None, min_length=1, max_length=255)
    degree: str | None = Field(None, min_length=1, max_length=255)
    field_of_study: str | None = Field(None, max_length=255)
    location: str | None = Field(None, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    currently_studying: bool | None = None
    cgpa: str | None = Field(None, max_length=20)

    @model_validator(mode="after")
    def _validate_dates(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError("End date must be on or after the start date")
        return self


class EducationResponse(EducationBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
