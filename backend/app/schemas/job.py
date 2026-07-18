from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class JobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    company_name: str = Field(..., min_length=1, max_length=255)
    company_url: str | None = None
    company_logo_url: str | None = None
    location: str | None = None
    description: str | None = None
    url: str | None = None
    source: str = Field(..., min_length=1, max_length=50)
    source_job_id: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    salary_period: str | None = None
    posted_at: datetime | None = None
    job_type: str | None = None
    remote: bool = False
    apply_url: str | None = None
    skills: list[str] = []
    requirements: list[str] = []
    benefits: list[str] = []
    categories: list[str] = []


class JobCreate(JobBase):
    content_hash: str = Field(..., min_length=1, max_length=64)
    raw_data: dict[str, Any] | None = None


class JobUpdate(BaseModel):
    is_active: bool | None = None
    viewed_at: datetime | None = None
    applied_at: datetime | None = None


class JobResponse(JobBase):
    id: str
    content_hash: str
    is_active: bool
    viewed_at: datetime | None = None
    applied_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobSearchParams(BaseModel):
    query: str = Field(default="", max_length=500)
    location: str | None = None
    remote_only: bool = False
    sources: list[str] | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    job_type: str | None = None
    skills: list[str] | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class JobSearchResponse(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class JobSearchRequest(BaseModel):
    query: str = ""
    location: str | None = None
    remote_only: bool = False
    sources: list[str] | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    job_type: str | None = None
    skills: list[str] | None = None
    page: int = 1
    page_size: int = 20


class ProviderStatus(BaseModel):
    name: str
    enabled: bool
    jobs_found: int | None = None
    error: str | None = None


class JobSearchResult(BaseModel):
    jobs: list[JobResponse]
    providers: list[ProviderStatus]
    total_new: int
    duplicates_removed: int
