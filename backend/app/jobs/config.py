from __future__ import annotations

from pydantic import BaseModel, Field


class AdzunaConfig(BaseModel):
    app_id: str = ""
    api_key: str = ""
    base_url: str = "https://api.adzuna.com/v1/api/jobs"
    page_size: int = Field(default=20, ge=1, le=50)
    rate_limit_rate: float = Field(default=5.0, ge=0, description="Requests per second")
    rate_limit_burst: int = Field(default=3, ge=1)


class WellfoundConfig(BaseModel):
    base_url: str = "https://api.angel.co/1"
    page_size: int = Field(default=20, ge=1, le=50)
    rate_limit_rate: float = Field(default=10.0, ge=0)
    rate_limit_burst: int = Field(default=5, ge=1)


class YCombinatorConfig(BaseModel):
    base_url: str = "https://www.workatastartup.com"
    page_size: int = Field(default=20, ge=1, le=50)
    rate_limit_rate: float = Field(default=10.0, ge=0)
    rate_limit_burst: int = Field(default=5, ge=1)


class GreenhouseConfig(BaseModel):
    base_url: str = "https://boards-api.greenhouse.io/v1/boards"
    page_size: int = Field(default=20, ge=1, le=50)
    rate_limit_rate: float = Field(default=10.0, ge=0)
    rate_limit_burst: int = Field(default=5, ge=1)


class LeverConfig(BaseModel):
    base_url: str = "https://api.lever.co/v0"
    page_size: int = Field(default=20, ge=1, le=50)
    rate_limit_rate: float = Field(default=10.0, ge=0)
    rate_limit_burst: int = Field(default=5, ge=1)


class AshbyConfig(BaseModel):
    base_url: str = "https://api.ashbyhq.com/posting-api"
    page_size: int = Field(default=20, ge=1, le=50)
    rate_limit_rate: float = Field(default=10.0, ge=0)
    rate_limit_burst: int = Field(default=5, ge=1)


class NaukriConfig(BaseModel):
    base_url: str = "https://www.naukri.com"
    page_size: int = Field(default=20, ge=1, le=50)
    rate_limit_rate: float = Field(default=5.0, ge=0)
    rate_limit_burst: int = Field(default=3, ge=1)


class FounditConfig(BaseModel):
    base_url: str = "https://www.foundit.in"
    page_size: int = Field(default=20, ge=1, le=50)
    rate_limit_rate: float = Field(default=5.0, ge=0)
    rate_limit_burst: int = Field(default=3, ge=1)


class InternshalaConfig(BaseModel):
    base_url: str = "https://internshala.com"
    page_size: int = Field(default=20, ge=1, le=50)
    rate_limit_rate: float = Field(default=10.0, ge=0)
    rate_limit_burst: int = Field(default=5, ge=1)


class FreshersworldConfig(BaseModel):
    base_url: str = "https://www.freshersworld.com"
    page_size: int = Field(default=20, ge=1, le=50)
    rate_limit_rate: float = Field(default=5.0, ge=0)
    rate_limit_burst: int = Field(default=3, ge=1)


class UnstopConfig(BaseModel):
    base_url: str = "https://unstop.com"
    page_size: int = Field(default=20, ge=1, le=50)
    rate_limit_rate: float = Field(default=10.0, ge=0)
    rate_limit_burst: int = Field(default=5, ge=1)


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
    wellfound: WellfoundConfig = Field(default_factory=WellfoundConfig)
    y_combinator: YCombinatorConfig = Field(default_factory=YCombinatorConfig)
    greenhouse: GreenhouseConfig = Field(default_factory=GreenhouseConfig)
    lever: LeverConfig = Field(default_factory=LeverConfig)
    ashby: AshbyConfig = Field(default_factory=AshbyConfig)
    naukri: NaukriConfig = Field(default_factory=NaukriConfig)
    foundit: FounditConfig = Field(default_factory=FounditConfig)
    internshala: InternshalaConfig = Field(default_factory=InternshalaConfig)
    freshersworld: FreshersworldConfig = Field(default_factory=FreshersworldConfig)
    unstop: UnstopConfig = Field(default_factory=UnstopConfig)
