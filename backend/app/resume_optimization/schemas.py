from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    REWRITTEN = "rewritten"
    REORDERED = "reordered"
    ADDED = "added"
    REMOVED = "removed"
    UNCHANGED = "unchanged"


class KeywordAnalysis(BaseModel):
    required_keywords: list[str] = Field(default_factory=list)
    preferred_keywords: list[str] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    industry_terms: list[str] = Field(default_factory=list)
    missing_required: list[str] = Field(default_factory=list)
    keyword_density: float = 0.0


class ChangeLogEntry(BaseModel):
    section: str
    change_type: ChangeType = ChangeType.UNCHANGED
    description: str | None = None
    original: str | None = None
    optimized: str | None = None


class ATSAssessment(BaseModel):
    overall_score: int = Field(default=0, ge=0, le=100)
    keyword_match: int = Field(default=0, ge=0, le=100)
    section_coverage: int = Field(default=0, ge=0, le=100)
    format_compatibility: int = Field(default=0, ge=0, le=100)
    keyword_placement: int = Field(default=0, ge=0, le=100)
    suggestions: list[str] = Field(default_factory=list)


class OptimizationSummary(BaseModel):
    original_ats_score: int = Field(default=0, ge=0, le=100)
    optimized_ats_score: int = Field(default=0, ge=0, le=100)
    sections_optimized: int = 0
    keywords_added: int = 0
    bullets_rewritten: int = 0
    items_reordered: int = 0


class OptimizedSection(BaseModel):
    section_type: str
    title: str | None = None
    original_content: str | None = None
    optimized_content: str | None = None
    change_type: ChangeType = ChangeType.UNCHANGED
    keywords_added: list[str] = Field(default_factory=list)


class OptimizedResume(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile_hash: str | None = None
    job_hash: str | None = None
    resume_hash: str | None = None

    professional_summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    experience_sections: list[OptimizedSection] = Field(default_factory=list)
    project_sections: list[OptimizedSection] = Field(default_factory=list)
    education_sections: list[OptimizedSection] = Field(default_factory=list)
    certification_sections: list[OptimizedSection] = Field(default_factory=list)
    other_sections: list[OptimizedSection] = Field(default_factory=list)

    keyword_analysis: KeywordAnalysis = Field(default_factory=KeywordAnalysis)
    ats_assessment: ATSAssessment = Field(default_factory=ATSAssessment)
    optimization_summary: OptimizationSummary = Field(default_factory=OptimizationSummary)
    change_log: list[ChangeLogEntry] = Field(default_factory=list)
