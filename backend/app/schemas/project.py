import uuid
from datetime import date, datetime

from pydantic import BaseModel


class ProjectBase(BaseModel):
    name: str
    description: str | None = None
    url: str | None = None
    github_url: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    url: str | None = None
    github_url: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None


class ProjectResponse(ProjectBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
