from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GreenhouseATSConfig(BaseModel):
    base_url: str = "https://boards.greenhouse.io"
    login_url: str = "https://app.greenhouse.io/users/sign_in"
    api_base: str = "https://boards-api.greenhouse.io/v1/boards"


class LeverATSConfig(BaseModel):
    base_url: str = "https://jobs.lever.co"
    login_url: str = "https://auth.lever.co/login"
    api_base: str = "https://api.lever.co/v1"


class AshbyATSConfig(BaseModel):
    base_url: str = "https://jobs.ashbyhq.com"
    login_url: str = ""
    api_base: str = "https://api.ashbyhq.com/posting-api"


class WorkdayATSConfig(BaseModel):
    base_url: str = "https://www.myworkdayjobs.com"
    login_url: str = ""
    api_base: str = ""


class SmartRecruitersATSConfig(BaseModel):
    base_url: str = "https://jobs.smartrecruiters.com"
    login_url: str = ""
    api_base: str = "https://api.smartrecruiters.com"


class BambooHRATSConfig(BaseModel):
    base_url: str = ""
    login_url: str = "https://{subdomain}.bamboohr.com/login.php"
    api_base: str = "https://api.bamboohr.com/api/gateway.php"


class RecruiteeATSConfig(BaseModel):
    base_url: str = "https://{company}.recruitee.com"
    login_url: str = "https://{company}.recruitee.com/sign_in"
    api_base: str = "https://api.recruitee.com"


class ATSConfig(BaseModel):
    default_timeout_ms: float = 60000.0
    default_headless: bool = True
    screenshot_on_error: bool = True
    screenshots_path: str = "screenshots"
    retry_attempts: int = 3
    retry_delay_seconds: float = 2.0

    greenhouse: GreenhouseATSConfig = Field(default_factory=GreenhouseATSConfig)
    lever: LeverATSConfig = Field(default_factory=LeverATSConfig)
    ashby: AshbyATSConfig = Field(default_factory=AshbyATSConfig)
    workday: WorkdayATSConfig = Field(default_factory=WorkdayATSConfig)
    smartrecruiters: SmartRecruitersATSConfig = Field(default_factory=SmartRecruitersATSConfig)
    bamboohr: BambooHRATSConfig = Field(default_factory=BambooHRATSConfig)
    recruitee: RecruiteeATSConfig = Field(default_factory=RecruiteeATSConfig)

    provider_configs: dict[str, dict[str, Any]] = Field(default_factory=dict)
