import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CompanyResearchRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=500)


class CompanyResearchResponse(BaseModel):
    id: uuid.UUID
    company_name: str
    industry: str | None = None
    mission: str | None = None
    values: list[str] = []
    products_or_services: list[str] = []
    company_culture: str | None = None
    recent_news: list[str] = []
    headquarters: str | None = None
    company_size: str | None = None
    linkedin_url: str | None = None
    hiring_trends: list[str] = []
    technology_stack: list[str] = []
    funding: dict | None = None
    summary: str | None = None
    cached_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CompanyResearchSummary(BaseModel):
    company_name: str
    summary: str | None
    cached_at: datetime | None = None

    model_config = {"from_attributes": True}
