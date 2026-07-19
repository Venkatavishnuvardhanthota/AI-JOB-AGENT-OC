import uuid

from pydantic import BaseModel, Field


class OptimizeResumeRequest(BaseModel):
    resume_version_id: uuid.UUID
    job_description: str = Field(..., min_length=10)
    company_name: str | None = None
    job_title: str | None = None
    target_ats_score: int | None = Field(default=None, ge=0, le=100)


class KeywordMatch(BaseModel):
    keyword: str
    category: str = "general"
    found: bool
    frequency: int = 0
    importance: str = "medium"


class SectionScore(BaseModel):
    section: str
    score: int = Field(..., ge=0, le=100)
    matched_keywords: list[KeywordMatch] = []
    missing_keywords: list[KeywordMatch] = []
    suggestions: list[str] = []


class AtsScoreResponse(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    section_scores: list[SectionScore] = []
    matched_keywords: list[KeywordMatch] = []
    missing_keywords: list[KeywordMatch] = []
    format_issues: list[str] = []
    recommendations: list[str] = []


class OptimizedSection(BaseModel):
    section: str
    original_text: str
    optimized_text: str
    keywords_added: list[str] = []
    keywords_kept: list[str] = []


class OptimizeResumeResponse(BaseModel):
    version_id: uuid.UUID
    ats_score: AtsScoreResponse
    optimized_sections: list[OptimizedSection] = []
    summary: str = ""


class KeywordSuggestion(BaseModel):
    keyword: str
    category: str = "general"
    suggested_section: str | None = None
    priority: str = "medium"
    reason: str = ""


class KeywordAnalysisRequest(BaseModel):
    resume_version_id: uuid.UUID
    job_description: str = Field(..., min_length=10)


class KeywordAnalysisResponse(BaseModel):
    job_keywords: list[KeywordSuggestion] = []
    present_in_resume: list[str] = []
    missing_from_resume: list[KeywordSuggestion] = []
    coverage_percentage: float = Field(..., ge=0.0, le=100.0)
    suggestions: list[str] = []


class AtsOptimizeRequest(BaseModel):
    resume_version_id: uuid.UUID
    job_description: str = Field(..., min_length=10)
    company_name: str | None = None
    job_title: str | None = None


class AtsOptimizeResponse(BaseModel):
    optimized_snapshot: dict
    changes_summary: str
    keywords_injected: list[str] = []
    score_improvement: int = 0
