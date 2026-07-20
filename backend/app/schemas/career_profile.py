import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.certification import CertificationResponse
from app.schemas.education import EducationResponse
from app.schemas.experience import ExperienceResponse
from app.schemas.job_preference import JobPreferenceResponse
from app.schemas.language import LanguageResponse
from app.schemas.project import ProjectResponse
from app.schemas.skill import SkillResponse


class CareerProfileResponse(BaseModel):
    id: uuid.UUID
    professional_summary: str | None = None
    portfolio_url: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    website_url: str | None = None
    education: list[EducationResponse] = []
    experience: list[ExperienceResponse] = []
    projects: list[ProjectResponse] = []
    skills: list[SkillResponse] = []
    certifications: list[CertificationResponse] = []
    languages: list[LanguageResponse] = []
    preferences: JobPreferenceResponse | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CareerProfileUpdate(BaseModel):
    professional_summary: str | None = None
    portfolio_url: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    website_url: str | None = None


class ProfileCompletenessResponse(BaseModel):
    percentage: int
    missing_sections: list[str]


class ResumeImportResponse(BaseModel):
    success: bool = True
    data: dict
    message: str = "Resume imported successfully. Review before saving."
