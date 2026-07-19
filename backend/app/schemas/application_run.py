import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ManualApplyRequest(BaseModel):
    job_ids: list[uuid.UUID] = Field(default_factory=list, max_length=50)
    schedule_id: uuid.UUID | None = None
    max_applications: int = Field(5, ge=1, le=50)


class RunResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    schedule_id: uuid.UUID | None = None
    status: str
    job_ids: list[uuid.UUID] = []
    applications_submitted_count: int = 0
    total_jobs_target: int = 0
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RunListItem(BaseModel):
    id: uuid.UUID
    status: str
    applications_submitted_count: int = 0
    total_jobs_target: int = 0
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
