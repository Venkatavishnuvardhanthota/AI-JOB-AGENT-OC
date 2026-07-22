from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MatchRecommendation(str, Enum):
    STRONG_APPLY = "strong_apply"
    APPLY = "apply"
    CONSIDER = "consider"
    WEAK = "weak"
    NOT_RECOMMENDED = "not_recommended"


class SkillMatchInfo(BaseModel):
    name: str
    matched: bool
    category: str | None = None
    proficiency: str | None = None
    normalized_name: str | None = None


class DimensionScore(BaseModel):
    score: float = Field(default=0.0, ge=0.0, le=100.0)
    weight: float = Field(default=0.0, ge=0.0)
    weighted_score: float = Field(default=0.0, ge=0.0, le=100.0)
    explanation: str | None = None
    details: dict | None = None


class MatchResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    profile_hash: str | None = None
    job_hash: str | None = None

    overall_match_score: float = Field(default=0.0, ge=0.0, le=100.0)
    recommendation: MatchRecommendation = MatchRecommendation.NOT_RECOMMENDED
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    match_summary: str | None = None
    improvement_recommendations: list[str] = Field(default_factory=list)

    matching_skills: list[SkillMatchInfo] = Field(default_factory=list)
    missing_skills: list[SkillMatchInfo] = Field(default_factory=list)
    preferred_skills: list[SkillMatchInfo] = Field(default_factory=list)

    skills_score: DimensionScore = Field(default_factory=DimensionScore)
    experience_score: DimensionScore = Field(default_factory=DimensionScore)
    education_score: DimensionScore = Field(default_factory=DimensionScore)
    location_score: DimensionScore = Field(default_factory=DimensionScore)
    remote_score: DimensionScore = Field(default_factory=DimensionScore)
    salary_score: DimensionScore = Field(default_factory=DimensionScore)
    employment_type_score: DimensionScore = Field(default_factory=DimensionScore)
    career_level_score: DimensionScore = Field(default_factory=DimensionScore)
    industry_score: DimensionScore = Field(default_factory=DimensionScore)
    certifications_score: DimensionScore = Field(default_factory=DimensionScore)
    projects_score: DimensionScore = Field(default_factory=DimensionScore)
