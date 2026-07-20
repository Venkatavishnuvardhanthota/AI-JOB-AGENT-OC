import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class JobPreferenceUpdate(BaseModel):
    preferred_titles: list[str] | None = None
    preferred_locations: list[str] | None = None
    employment_types: list[str] | None = None
    work_modes: list[str] | None = None
    minimum_salary: float | None = None
    preferred_currency: str | None = Field(None, max_length=10)


class JobPreferenceResponse(BaseModel):
    id: uuid.UUID
    preferred_titles: list[str] = []
    preferred_locations: list[str] = []
    employment_types: list[str] = []
    work_modes: list[str] = []
    minimum_salary: float | None = None
    preferred_currency: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
