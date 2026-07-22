from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CoverLetterSection(BaseModel):
    section_type: str
    content: str
    source_fields: list[str] = Field(default_factory=list)


class PersonalizationData(BaseModel):
    company_name: str | None = None
    job_title: str | None = None
    hiring_manager: str | None = None
    user_name: str | None = None
    current_role: str | None = None
    years_experience: float | None = None
    career_level: str | None = None
    primary_skills: list[str] = Field(default_factory=list)
    matching_skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    education_summary: str | None = None
    certifications: list[str] = Field(default_factory=list)
    industries: list[str] = Field(default_factory=list)
    career_goals: str | None = None
    personal_summary: str | None = None
    reason_for_interest: str | None = None


class GeneratedCoverLetter(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile_hash: str | None = None
    job_hash: str | None = None
    resume_hash: str | None = None

    greeting: str | None = None
    opening_paragraph: str | None = None
    company_paragraph: str | None = None
    experience_paragraph: str | None = None
    skills_paragraph: str | None = None
    projects_paragraph: str | None = None
    closing_paragraph: str | None = None
    signature: str | None = None

    full_text: str | None = None
    sections: list[CoverLetterSection] = Field(default_factory=list)
    personalization: PersonalizationData = Field(default_factory=PersonalizationData)
    configuration: dict = Field(default_factory=dict)
    word_count: int = 0
    warnings: list[str] = Field(default_factory=list)
