import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class EducationBase(BaseModel):
    institution: str
    degree: str
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    gpa: float | None = Field(None, ge=0.0, le=4.0)
    description: str | None = None


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    gpa: float | None = Field(None, ge=0.0, le=4.0)
    description: str | None = None


class EducationResponse(EducationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
