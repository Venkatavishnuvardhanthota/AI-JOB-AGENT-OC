from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class CareerLevel(str, Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"
    UNKNOWN = "unknown"


class Availability(str, Enum):
    IMMEDIATE = "immediate"
    TWO_WEEKS = "two_weeks"
    ONE_MONTH = "one_month"
    TWO_MONTHS = "two_months"
    THREE_MONTHS = "three_months"
    NOT_AVAILABLE = "not_available"
    UNKNOWN = "unknown"


class LanguageInfo(BaseModel):
    language: str
    proficiency: str | None = None


class TechnicalStack(BaseModel):
    programming_languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    cloud_platforms: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)


class ProfileCompleteness(BaseModel):
    overall_score: int = Field(default=0, ge=0, le=100)
    categories: dict[str, int] = Field(default_factory=dict)
    missing_items: list[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    field: str
    severity: str = Field(default="warning", pattern="^(info|warning|error)$")
    message: str


class ValidationReport(BaseModel):
    issues: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class UserIntelligenceProfile(BaseModel):
    user_id: uuid.UUID
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    personal_summary: str | None = None
    current_role: str | None = None
    career_level: CareerLevel = CareerLevel.UNKNOWN
    years_of_experience: float | None = None
    primary_skills: list[str] = Field(default_factory=list)
    secondary_skills: list[str] = Field(default_factory=list)
    technical_stack: TechnicalStack = Field(default_factory=TechnicalStack)
    education_summary: str | None = None
    certifications: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    remote_preference: bool | None = None
    employment_preference: str | None = None
    salary_expectation: str | None = None
    languages: list[LanguageInfo] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    skill_gaps: list[str] = Field(default_factory=list)
    career_goals: str | None = None
    availability: Availability = Availability.UNKNOWN
    completeness: ProfileCompleteness = Field(default_factory=ProfileCompleteness)
    validation: ValidationReport = Field(default_factory=ValidationReport)
    profile_hash: str | None = None
