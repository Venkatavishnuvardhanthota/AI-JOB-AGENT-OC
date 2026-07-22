from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CompanyType(str, Enum):
    STARTUP = "startup"
    ENTERPRISE = "enterprise"
    CONSULTING = "consulting"
    PRODUCT_COMPANY = "product_company"
    SERVICE_COMPANY = "service_company"
    GOVERNMENT = "government"
    NON_PROFIT = "non_profit"
    UNKNOWN = "unknown"


class HiringPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class RoleSeniority(str, Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"
    UNKNOWN = "unknown"


class RoleCategory(str, Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    FULL_STACK = "full_stack"
    DATA_ANALYST = "data_analyst"
    DATA_SCIENTIST = "data_scientist"
    ML_ENGINEER = "ml_engineer"
    DEVOPS = "devops"
    CLOUD = "cloud"
    QA = "qa"
    MOBILE = "mobile"
    UI_UX = "ui_ux"
    CYBER_SECURITY = "cyber_security"
    GENERAL_SOFTWARE_ENGINEER = "general_software_engineer"
    UNKNOWN = "unknown"


class ApplicationPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CompanyIntelligence(BaseModel):
    summary: str | None = None
    industry_classification: str | None = None
    company_size: str | None = None
    company_type: CompanyType = CompanyType.UNKNOWN
    is_startup: bool | None = None
    remote_policy: str | None = None
    hiring_priority: HiringPriority = HiringPriority.UNKNOWN


class SkillExtraction(BaseModel):
    programming_languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    cloud_platforms: list[str] = Field(default_factory=list)
    developer_tools: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    all_skills: list[str] = Field(default_factory=list)


class ResponsibilityExtraction(BaseModel):
    primary: list[str] = Field(default_factory=list)
    secondary: list[str] = Field(default_factory=list)
    leadership: list[str] = Field(default_factory=list)
    communication: list[str] = Field(default_factory=list)
    customer_facing: list[str] = Field(default_factory=list)
    mentoring: list[str] = Field(default_factory=list)


class RequirementAnalysis(BaseModel):
    required: list[str] = Field(default_factory=list)
    preferred: list[str] = Field(default_factory=list)
    optional: list[str] = Field(default_factory=list)
    unknown: list[str] = Field(default_factory=list)


class RoleIntelligence(BaseModel):
    summary: str | None = None
    seniority: RoleSeniority = RoleSeniority.UNKNOWN
    category: RoleCategory = RoleCategory.UNKNOWN
    skills: SkillExtraction = Field(default_factory=SkillExtraction)
    responsibilities: ResponsibilityExtraction = Field(default_factory=ResponsibilityExtraction)
    qualifications: RequirementAnalysis = Field(default_factory=RequirementAnalysis)
    education_requirements: list[str] = Field(default_factory=list)
    certification_requirements: list[str] = Field(default_factory=list)
    travel_requirements: str | None = None
    visa_sponsorship_mentioned: bool | None = None


class SalaryAnalysis(BaseModel):
    min_amount: float | None = None
    max_amount: float | None = None
    currency: str | None = None
    period: str | None = None
    is_competitive: bool | None = None
    has_conflicts: bool = False


class LocationAnalysis(BaseModel):
    city: str | None = None
    state: str | None = None
    country: str | None = None
    remote_type: str | None = None
    is_remote_possible: bool | None = None
    has_conflicts: bool = False


class ValidationResult(BaseModel):
    has_missing_description: bool = False
    has_incomplete_posting: bool = False
    duplicate_requirements: list[str] = Field(default_factory=list)
    conflicting_salary: bool = False
    conflicting_location: bool = False
    invalid_employment_type: bool = False
    warnings: list[str] = Field(default_factory=list)


class ApplicationIntelligence(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    job_hash: str | None = None
    profile_hash: str | None = None

    company: CompanyIntelligence = Field(default_factory=CompanyIntelligence)
    role: RoleIntelligence = Field(default_factory=RoleIntelligence)
    salary: SalaryAnalysis = Field(default_factory=SalaryAnalysis)
    location: LocationAnalysis = Field(default_factory=LocationAnalysis)
    validation: ValidationResult = Field(default_factory=ValidationResult)

    application_priority: ApplicationPriority = ApplicationPriority.LOW
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)

    raw_employment_type: str | None = None
    employment_type_analysis: str | None = None
