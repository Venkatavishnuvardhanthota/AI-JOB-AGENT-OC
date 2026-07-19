import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BehavioralQuestion(BaseModel):
    question: str
    situation: str
    task: str
    action: str
    result: str
    category: str = "general"


class TechnicalQuestion(BaseModel):
    question: str
    topic: str
    difficulty: str = "medium"
    answer: str
    key_concepts: list[str] = []


class SalaryExpectation(BaseModel):
    market_range_min: float | None = None
    market_range_max: float | None = None
    recommended: float | None = None
    currency: str = "USD"
    factors: list[str] = []
    negotiation_tips: list[str] = []


class NoticePeriodInfo(BaseModel):
    current_period_weeks: int | None = None
    negotiable: bool = True
    negotiation_tips: list[str] = []
    standard_in_industry: str | None = None


class StrengthItem(BaseModel):
    strength: str
    evidence: str
    relevance_to_role: str
    category: str = "technical"


class WeaknessItem(BaseModel):
    weakness: str
    improvement_plan: str
    positive_framing: str
    category: str = "skill"


class CareerGoal(BaseModel):
    short_term: str
    long_term: str
    alignment_with_company: str
    timeline_years: int | None = None


class CompanySpecificAnswer(BaseModel):
    question: str
    context: str
    suggested_answer: str
    research_source: str | None = None


class TruthValidationResult(BaseModel):
    statement: str
    is_consistent: bool
    confidence: float = 0.0
    inconsistencies: list[str] = []
    suggestions: list[str] = []


class InterviewPrepGenerateRequest(BaseModel):
    job_title: str = Field(..., min_length=1, max_length=500)
    company_name: str = Field(..., min_length=1, max_length=500)
    job_description: str = Field(..., min_length=10)
    resume_snapshot: dict | None = None
    company_research: dict | None = None
    include_behavioral: bool = True
    include_technical: bool = True
    include_salary: bool = True
    include_notice_period: bool = True
    include_strengths_weaknesses: bool = True
    include_career_goals: bool = True
    include_company_specific: bool = True


class InterviewPrepResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_title: str
    company_name: str
    behavioral_questions: list[BehavioralQuestion] = []
    technical_questions: list[TechnicalQuestion] = []
    salary_expectation: SalaryExpectation | None = None
    notice_period: NoticePeriodInfo | None = None
    strengths: list[StrengthItem] = []
    weaknesses: list[WeaknessItem] = []
    career_goals: CareerGoal | None = None
    company_specific_answers: list[CompanySpecificAnswer] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InterviewPrepListItem(BaseModel):
    id: uuid.UUID
    job_title: str
    company_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TruthValidateRequest(BaseModel):
    statements: list[str] = Field(..., min_length=1, max_length=50)
    context: str | None = None


class TruthValidateResponse(BaseModel):
    results: list[TruthValidationResult]
