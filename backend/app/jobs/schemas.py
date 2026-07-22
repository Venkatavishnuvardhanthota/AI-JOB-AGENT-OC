from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"
    OTHER = "other"


class RemoteType(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ON_SITE = "on_site"
    UNKNOWN = "unknown"


class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"
    UNKNOWN = "unknown"


class SalaryInfo(BaseModel):
    min_amount: float | None = Field(default=None, ge=0)
    max_amount: float | None = Field(default=None, ge=0)
    currency: str = Field(default="USD", min_length=1)
    period: str = Field(default="yearly", description="yearly, monthly, hourly")
    interval: str | None = Field(default=None, description="Display interval text")


class LocationInfo(BaseModel):
    city: str | None = None
    state: str | None = None
    country: str | None = None
    remote_type: RemoteType = RemoteType.UNKNOWN
    display_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class CompanyInfo(BaseModel):
    name: str = Field(min_length=1)
    website: str | None = None
    logo_url: str | None = None
    description: str | None = None
    industry: str | None = None
    size: str | None = None


class JobPosting(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    provider_job_id: str | None = Field(default=None, description="Provider-specific job ID")
    title: str = Field(min_length=1)
    company: CompanyInfo
    location: LocationInfo = Field(default_factory=LocationInfo)
    description: str | None = None
    description_html: str | None = None
    url: str | None = None
    apply_url: str | None = None
    employment_type: EmploymentType = EmploymentType.OTHER
    experience_level: ExperienceLevel = ExperienceLevel.UNKNOWN
    salary: SalaryInfo | None = None
    skills: list[str] = Field(default_factory=list)
    posted_date: datetime | None = None
    expiration_date: datetime | None = None
    provider: str = Field(min_length=1)
    source_updated_at: datetime | None = None
    normalized_at: datetime = Field(default_factory=datetime.utcnow)


class JobSearchRequest(BaseModel):
    query: str | None = Field(default=None, max_length=500)
    keywords: list[str] = Field(default_factory=list)
    location: str | None = Field(default=None, max_length=200)
    remote_only: bool | None = None
    employment_type: EmploymentType | None = None
    experience_level: ExperienceLevel | None = None
    salary_min: float | None = Field(default=None, ge=0)
    salary_max: float | None = Field(default=None, ge=0)
    providers: list[str] | None = Field(default=None, description="Specific providers to query")
    limit: int = Field(default=25, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    deduplicate: bool = True
    posted_within_days: int | None = Field(default=None, ge=1)


class SearchMetadata(BaseModel):
    total_results: int = 0
    returned_results: int = 0
    providers_queried: list[str] = Field(default_factory=list)
    providers_succeeded: list[str] = Field(default_factory=list)
    providers_failed: list[dict] = Field(default_factory=list)
    duplicates_removed: int = 0
    filters_applied: list[str] = Field(default_factory=list)
    search_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    duration_ms: int | None = None


class JobSearchResponse(BaseModel):
    results: list[JobPosting] = Field(default_factory=list)
    metadata: SearchMetadata = Field(default_factory=SearchMetadata)


class JobProviderInfo(BaseModel):
    name: str
    display_name: str
    description: str | None = None
    is_available: bool = False
    supports_pagination: bool = False
    supports_filters: bool = False
    version: str = "0.1.0"
