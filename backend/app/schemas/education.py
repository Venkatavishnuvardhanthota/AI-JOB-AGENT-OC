import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class EducationBase(BaseModel):
    institution: str = Field(max_length=255)
    degree: str = Field(max_length=255)
    field_of_study: str | None = Field(None, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    grade: str | None = Field(None, max_length=50)
    description: str | None = None


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    institution: str | None = Field(None, max_length=255)
    degree: str | None = Field(None, max_length=255)
    field_of_study: str | None = Field(None, max_length=255)
    start_date: date | None = None
    end_date: date | None = None
    grade: str | None = Field(None, max_length=50)
    description: str | None = None


class EducationResponse(EducationBase):
    id: uuid.UUID
    profile_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
