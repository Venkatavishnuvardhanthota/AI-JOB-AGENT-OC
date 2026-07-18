import uuid
from datetime import date, datetime

from pydantic import BaseModel


class ExperienceBase(BaseModel):
    company: str
    title: str
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    description: str | None = None
    company_url: str | None = None


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(BaseModel):
    company: str | None = None
    title: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    description: str | None = None
    company_url: str | None = None


class ExperienceResponse(ExperienceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
