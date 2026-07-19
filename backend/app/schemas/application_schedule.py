import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ScheduleCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    schedule_type: str = Field(..., pattern="^(daily|weekly|custom)$")
    cron_expression: str | None = Field(None, max_length=255)
    timezone: str = "UTC"
    max_applications_per_day: int = Field(10, ge=1, le=100)
    days_of_week: list[int] | None = None
    time_of_day: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")


class ScheduleUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    schedule_type: str | None = Field(None, pattern="^(daily|weekly|custom)$")
    cron_expression: str | None = None
    timezone: str | None = None
    max_applications_per_day: int | None = Field(None, ge=1, le=100)
    days_of_week: list[int] | None = None
    time_of_day: str | None = None


class ScheduleResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    status: str
    schedule_type: str
    cron_expression: str | None = None
    timezone: str
    max_applications_per_day: int
    days_of_week: list[int] = []
    time_of_day: str | None = None
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScheduleListItem(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    schedule_type: str
    max_applications_per_day: int
    next_run_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
