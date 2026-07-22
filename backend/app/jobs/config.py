from __future__ import annotations

from pydantic import BaseModel, Field


class AdzunaConfig(BaseModel):
    app_id: str = ""
    api_key: str = ""
    base_url: str = "https://api.adzuna.com/v1/api/jobs"
    page_size: int = Field(default=20, ge=1, le=50)
    rate_limit_rate: float = Field(default=5.0, ge=0, description="Requests per second")
    rate_limit_burst: int = Field(default=3, ge=1)


class JobDiscoveryConfig(BaseModel):
    enabled_providers: list[str] = Field(
        default_factory=list, description="List of enabled job provider names"
    )
    request_timeout_seconds: int = Field(default=30, ge=1, description="Provider request timeout")
    retry_count: int = Field(default=2, ge=0, description="Retry attempts on transient failure")
    default_search_limit: int = Field(default=25, ge=1, le=100, description="Default max results per provider")
    dedup_by_url: bool = Field(default=True, description="Deduplicate by job URL")
    dedup_by_provider_id: bool = Field(default=True, description="Deduplicate by provider job ID")
    dedup_by_title_company_location: bool = Field(
        default=False, description="Deduplicate by title+company+location (may use fuzzy matching)"
    )
    dedup_field_weight_title: float = Field(default=0.5, ge=0.0, le=1.0)
    dedup_field_weight_company: float = Field(default=0.3, ge=0.0, le=1.0)
    dedup_field_weight_location: float = Field(default=0.2, ge=0.0, le=1.0)
    adzuna: AdzunaConfig = Field(default_factory=AdzunaConfig)
