from datetime import datetime

from pydantic import BaseModel, Field


class SkillScore(BaseModel):
    matched: list[str] = []
    missing: list[str] = []
    total_user: int = 0
    total_job: int = 0
    score: float = 0.0


class KeywordScore(BaseModel):
    extracted: list[str] = []
    matched: list[str] = []
    total: int = 0
    score: float = 0.0


class ExperienceScore(BaseModel):
    user_years: float = 0.0
    required_years: float | None = None
    has_relevant: bool = False
    relevant_titles: list[str] = []
    score: float = 0.0


class EducationScore(BaseModel):
    user_level: str = "unknown"
    required_level: str | None = None
    user_field: str | None = None
    required_field: str | None = None
    level_match: bool = False
    field_match: bool = False
    score: float = 0.0


class CompanyScore(BaseModel):
    company_name: str = ""
    is_blacklisted: bool = False
    has_connections: bool = False
    score: float = 0.0


class ScoreExplanation(BaseModel):
    category: str
    score: float
    weight: float
    details: str


class MatchScore(BaseModel):
    overall: float = 0.0
    skill: SkillScore = SkillScore()
    keyword: KeywordScore = KeywordScore()
    experience: ExperienceScore = ExperienceScore()
    education: EducationScore = EducationScore()
    company: CompanyScore = CompanyScore()
    explanations: list[ScoreExplanation] = []
    scored_at: datetime | None = None
    job_id: str | None = None


class ScoringWeights(BaseModel):
    skill: float = 0.35
    keyword: float = 0.15
    experience: float = 0.25
    education: float = 0.15
    company: float = 0.10


class ScoringConfig(BaseModel):
    weights: ScoringWeights = ScoringWeights()
    skill_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    keyword_threshold: float = Field(default=0.1, ge=0.0, le=1.0)
    experience_threshold: float = Field(default=0.2, ge=0.0, le=1.0)
    education_threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_threshold: float = Field(default=0.4, ge=0.0, le=1.0)
    boost_exact_title_match: bool = True
    boost_current_company: bool = True
    penalty_blacklisted: bool = True


class ScoringConfigResponse(BaseModel):
    config: ScoringConfig
    updated_at: datetime | None = None


class BatchScoreRequest(BaseModel):
    job_ids: list[str] = Field(..., min_length=1, max_length=50)


class BatchScoreResponse(BaseModel):
    scores: list[MatchScore]


class ScoredJobResponse(BaseModel):
    id: str
    title: str
    company_name: str
    location: str | None = None
    source: str
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    job_type: str | None = None
    remote: bool = False
    posted_at: datetime | None = None
    skills: list[str] = []
    is_active: bool = True
    match_score: float = 0.0
    match_details: ScoreExplanation | None = None
