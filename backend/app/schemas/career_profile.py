import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.certification import CertificationResponse
from app.schemas.education import EducationResponse
from app.schemas.experience import ExperienceResponse
from app.schemas.job_preference import JobPreferenceResponse
from app.schemas.language import LanguageResponse
from app.schemas.project import ProjectResponse
from app.schemas.skill import SkillResponse
from app.schemas.social_link import SocialLinkResponse


class CareerProfileResponse(BaseModel):
    id: uuid.UUID
    headline: str | None = None
    professional_summary: str | None = None
    total_years_experience: float | None = None
    current_role: str | None = None
    desired_role: str | None = None
    employment_status: str | None = None
    current_salary: float | None = None
    expected_salary: float | None = None
    willing_to_relocate: bool | None = None
    visa_sponsorship_requirement: bool | None = None
    notice_period: str | None = None
    portfolio_url: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    website_url: str | None = None
    profile_completeness: int | None = None
    education: list[EducationResponse] = []
    experience: list[ExperienceResponse] = []
    projects: list[ProjectResponse] = []
    skills: list[SkillResponse] = []
    certifications: list[CertificationResponse] = []
    languages: list[LanguageResponse] = []
    social_links: list[SocialLinkResponse] = []
    preferences: JobPreferenceResponse | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CareerProfileUpdate(BaseModel):
    headline: str | None = Field(None, max_length=255)
    professional_summary: str | None = None
    total_years_experience: float | None = Field(None, ge=0, le=100)
    current_role: str | None = Field(None, max_length=255)
    desired_role: str | None = Field(None, max_length=255)
    employment_status: str | None = Field(None, max_length=50)
    current_salary: float | None = Field(None, ge=0)
    expected_salary: float | None = Field(None, ge=0)
    willing_to_relocate: bool | None = None
    visa_sponsorship_requirement: bool | None = None
    notice_period: str | None = Field(None, max_length=100)
    portfolio_url: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    website_url: str | None = None

    @field_validator("portfolio_url", "linkedin_url", "github_url", "website_url")
    @classmethod
    def validate_urls(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class ProfileCompletenessResponse(BaseModel):
    percentage: int
    breakdown: dict[str, int]
    missing_sections: list[str]


class ResumeImportResponse(BaseModel):
    success: bool = True
    data: dict
    message: str = "Resume imported successfully. Review before saving."
