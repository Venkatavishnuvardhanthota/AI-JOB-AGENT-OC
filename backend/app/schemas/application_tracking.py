import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# ── Application ──


class ApplicationCreateRequest(BaseModel):
    job_posting_id: uuid.UUID
    job_title: str = Field(..., min_length=1, max_length=500)
    company_name: str = Field(..., min_length=1, max_length=500)
    job_url: str | None = Field(None, max_length=2000)
    location: str | None = Field(None, max_length=255)
    salary_range: str | None = Field(None, max_length=255)
    status: str = "saved"
    notes: str | None = None
    tag_ids: list[uuid.UUID] = []


class ApplicationUpdateRequest(BaseModel):
    status: str | None = None
    job_title: str | None = Field(None, min_length=1, max_length=500)
    company_name: str | None = Field(None, min_length=1, max_length=500)
    job_url: str | None = None
    location: str | None = None
    salary_range: str | None = None
    is_active: bool | None = None


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_posting_id: uuid.UUID | None = None
    run_id: uuid.UUID | None = None
    status: str
    job_title: str
    company_name: str
    job_url: str | None = None
    location: str | None = None
    salary_range: str | None = None
    applied_at: datetime | None = None
    is_active: bool = True
    tags: list["TagResponse"] = []
    note_count: int = 0
    last_timeline_event: "TimelineEventResponse | None" = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationListItem(BaseModel):
    id: uuid.UUID
    job_posting_id: uuid.UUID | None = None
    status: str
    job_title: str
    company_name: str
    location: str | None = None
    applied_at: datetime | None = None
    is_active: bool = True
    tags: list["TagResponse"] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Notes ──


class NoteCreateRequest(BaseModel):
    content: str = Field(..., min_length=1)


class NoteResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Tags ──


class TagCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")


class TagUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    color: str | None = None


class TagResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    color: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Timeline ──


class TimelineEventResponse(BaseModel):
    id: uuid.UUID
    application_id: uuid.UUID
    event_type: str
    description: str
    occurred_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Analytics ──


class StatusCount(BaseModel):
    status: str
    count: int


class TopCompany(BaseModel):
    company_name: str
    count: int


class ApplicationAnalytics(BaseModel):
    total_applications: int
    status_breakdown: list[StatusCount] = []
    top_companies: list[TopCompany] = []
    applications_this_week: int = 0
    applications_this_month: int = 0
    active_applications: int = 0
    interview_rate: float = 0.0
    success_rate: float = 0.0


# ── Filters ──


class ApplicationFilterParams(BaseModel):
    status: str | None = None
    company_name: str | None = None
    search: str | None = None
    tag_ids: list[uuid.UUID] = []
    date_from: datetime | None = None
    date_to: datetime | None = None
    is_active: bool | None = None
    skip: int = 0
    limit: int = 50
