import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class JobSearchParams(BaseModel):
    search: str | None = None
    location: str | None = None
    remote: bool | None = None
    employment_type: str | None = None
    experience_level: str | None = None
    provider: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
    sort: str | None = None


class JobResponse(BaseModel):
    id: uuid.UUID
    provider: str
    title: str
    company: str
    location: str | None
    description: str | None
    employment_type: str | None
    salary_min: float | None
    salary_max: float | None
    currency: str | None
    application_url: str | None
    posted_at: datetime | None
    match_score: float | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobSearchResponse(BaseModel):
    data: list[JobResponse]
    pagination: dict


class JobMatchResponse(BaseModel):
    score: float
    confidence: float
    strengths: list[str]
    skill_gaps: list[str]
    summary: str


class CompanyInsightResponse(BaseModel):
    company: str
    industry: str | None
    size: str | None
    summary: str | None
    culture: str | None
    headquarters: str | None


class ProviderResponse(BaseModel):
    name: str
    status: str
