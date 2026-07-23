from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ATSProviderState(str, Enum):
    UNKNOWN = "unknown"
    DETECTED = "detected"
    CONNECTED = "connected"
    LOGGED_IN = "logged_in"
    NAVIGATING = "navigating"
    ON_JOB = "on_job"
    APPLYING = "applying"
    SUBMITTED = "submitted"
    ERROR = "error"
    CLOSED = "closed"


class ATSProviderCapability(str, Enum):
    JOB_SEARCH = "job_search"
    JOB_DETAILS = "job_details"
    APPLY = "apply"
    UPLOAD_RESUME = "upload_resume"
    UPLOAD_COVER_LETTER = "upload_cover_letter"
    AUTO_FILL = "auto_fill"
    LOGIN = "login"
    LOGOUT = "logout"
    SCREENSHOT = "screenshot"
    VALIDATE = "validate"
    DETECT = "detect"


class ATSProviderMetadata(BaseModel):
    name: str
    display_name: str
    description: str = ""
    version: str = "0.1.0"
    homepage_url: str = ""
    capabilities: list[ATSProviderCapability] = Field(default_factory=list)
    url_patterns: list[str] = Field(default_factory=list)
    requires_auth: bool = False
    requires_login: bool = False
    max_file_size_mb: int = 10
    allowed_file_types: list[str] = Field(default_factory=lambda: [".pdf", ".doc", ".docx", ".txt", ".rtf"])


class ATSDetectionResult(BaseModel):
    provider_name: str
    provider_display_name: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    matched_pattern: str | None = None
    url: str


class ATSLoginRequest(BaseModel):
    email: str | None = None
    password: str | None = None
    api_key: str | None = None
    sso_token: str | None = None
    credentials: dict[str, str] = Field(default_factory=dict)


class ATSLoginResult(BaseModel):
    success: bool
    session_id: str | None = None
    message: str | None = None
    requires_mfa: bool = False
    mfa_method: str | None = None


class ATSNavigationRequest(BaseModel):
    url: str
    timeout_ms: float = 60000.0
    wait_until: str = "load"
    wait_for_selector: str | None = None


class ATSNavigationResult(BaseModel):
    success: bool
    url: str
    title: str | None = None
    duration_ms: float = 0.0
    error: str | None = None


class ATSJobSearchRequest(BaseModel):
    query: str | None = None
    location: str | None = None
    department: str | None = None
    category: str | None = None
    offset: int = 0
    limit: int = 20


class ATSJobInfo(BaseModel):
    provider_job_id: str
    title: str
    url: str
    location: str | None = None
    department: str | None = None
    description: str | None = None
    apply_url: str | None = None
    posted_date: str | None = None
    employment_type: str | None = None
    experience_level: str | None = None


class ATSApplicationRequest(BaseModel):
    job_id: str
    job_url: str
    resume_path: str | None = None
    cover_letter_path: str | None = None
    additional_documents: list[str] = Field(default_factory=list)
    fields: dict[str, str] = Field(default_factory=dict)


class ATSApplicationResult(BaseModel):
    success: bool
    application_id: str | None = None
    confirmation_url: str | None = None
    message: str | None = None
    errors: list[str] = Field(default_factory=list)
    screenshot_path: str | None = None


class ATSProviderInfo(BaseModel):
    name: str
    display_name: str
    description: str = ""
    version: str = "0.1.0"
    homepage_url: str = ""
    capabilities: list[str] = Field(default_factory=list)
    url_patterns: list[str] = Field(default_factory=list)
    requires_auth: bool = False
    requires_login: bool = False


class ATSValidationResult(BaseModel):
    valid: bool
    provider_name: str | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    detected_elements: dict[str, bool] = Field(default_factory=dict)


class ATSProviderConfig(BaseModel):
    name: str
    enabled: bool = True
    headless: bool = True
    timeout_ms: float = 60000.0
    retry_attempts: int = 3
    retry_delay_seconds: float = 2.0
    credentials: dict[str, str] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)
