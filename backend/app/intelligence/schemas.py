from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AnalyticsType(str, Enum):
    APPLICATION_SUCCESS_RATE = "application_success_rate"
    PROVIDER_SUCCESS_RATE = "provider_success_rate"
    RESUME_EFFECTIVENESS = "resume_effectiveness"
    COVER_LETTER_EFFECTIVENESS = "cover_letter_effectiveness"
    JOB_SOURCE_EFFECTIVENESS = "job_source_effectiveness"
    SALARY_TRENDS = "salary_trends"
    LOCATION_TRENDS = "location_trends"
    INDUSTRY_TRENDS = "industry_trends"
    COMPANY_TRENDS = "company_trends"
    RESPONSE_TIME = "response_time"
    ACCEPTANCE_RATE = "acceptance_rate"
    REJECTION_RATE = "rejection_rate"


class RecommendationType(str, Enum):
    BEST_RESUME = "best_resume"
    BEST_COVER_LETTER = "best_cover_letter"
    BEST_PROVIDER = "best_provider"
    BEST_STRATEGY = "best_strategy"
    BEST_TIMING = "best_timing"
    BEST_AI_MODEL = "best_ai_model"
    BEST_PROMPT_TEMPLATE = "best_prompt_template"
    BEST_RETRY_STRATEGY = "best_retry_strategy"


class LearningEventType(str, Enum):
    SUCCESSFUL_APPLICATION = "successful_application"
    FAILED_APPLICATION = "failed_application"
    MANUAL_INTERVENTION = "manual_intervention"
    RESUME_PERFORMANCE = "resume_performance"
    AI_OUTPUT = "ai_output"
    PROVIDER_RELIABILITY = "provider_reliability"
    MATCHING_QUALITY = "matching_quality"
    WORKFLOW_HISTORY = "workflow_history"


class OptimizationType(str, Enum):
    MATCH_OPTIMIZATION = "match_optimization"
    PROMPT_OPTIMIZATION = "prompt_optimization"
    PROVIDER_OPTIMIZATION = "provider_optimization"
    STRATEGY_OPTIMIZATION = "strategy_optimization"


class ScoreModel(str, Enum):
    RESUME_QUALITY = "resume_quality"
    APPLICATION_QUALITY = "application_quality"
    PROVIDER_QUALITY = "provider_quality"
    JOB_QUALITY = "job_quality"
    WORKFLOW_QUALITY = "workflow_quality"


class FeedbackCategory(str, Enum):
    GOOD_RECOMMENDATION = "good_recommendation"
    BAD_RECOMMENDATION = "bad_recommendation"
    SUCCESSFUL_APPLICATION = "successful_application"
    FAILED_APPLICATION = "failed_application"
    MANUAL_RATING = "manual_rating"


class ExperimentType(str, Enum):
    A_B_PROMPT = "a_b_prompt"
    RESUME_COMPARISON = "resume_comparison"
    COVER_LETTER_COMPARISON = "cover_letter_comparison"
    PROVIDER_COMPARISON = "provider_comparison"
    STRATEGY_COMPARISON = "strategy_comparison"


class AnalyticsResult(BaseModel):
    type: AnalyticsType
    value: float = 0.0
    label: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    sample_size: int = 0
    period_start: datetime | None = None
    period_end: datetime | None = None
    computed_at: datetime = Field(default_factory=datetime.utcnow)


class RecommendationResult(BaseModel):
    type: RecommendationType
    recommended_value: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    alternatives: list[str] = Field(default_factory=list)
    reasoning: str = ""
    supporting_data: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LearningEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: LearningEventType
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "intelligence"


class OptimizationResult(BaseModel):
    type: OptimizationType
    recommendations: list[str] = Field(default_factory=list)
    improvements: dict[str, float] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScoreResult(BaseModel):
    model: ScoreModel
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    weights: dict[str, float] = Field(default_factory=dict)
    components: dict[str, float] = Field(default_factory=dict)
    label: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    computed_at: datetime = Field(default_factory=datetime.utcnow)


class FeedbackRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: FeedbackCategory
    rating: float | None = Field(default=None, ge=0.0, le=5.0)
    comment: str | None = None
    recommendation_id: str | None = None
    application_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HistoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    description: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "intelligence"


class ExperimentResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ExperimentType
    variant_a: str = ""
    variant_b: str = ""
    winner: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    metrics: dict[str, dict[str, float]] = Field(default_factory=dict)
    sample_size: int = 0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class WeightedScore(BaseModel):
    name: str
    weight: float = Field(default=1.0, ge=0.0)
    score: float = Field(default=0.0, ge=0.0, le=1.0)


class ProviderScore(BaseModel):
    provider_name: str
    availability: float = Field(default=0.0, ge=0.0, le=1.0)
    latency: float = Field(default=0.0, ge=0.0)
    cost: float = Field(default=0.0, ge=0.0)
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class PromptScore(BaseModel):
    template_name: str
    quality: float = Field(default=0.0, ge=0.0, le=1.0)
    latency: float = Field(default=0.0, ge=0.0)
    cost: float = Field(default=0.0, ge=0.0)
    token_usage: int = 0
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_score: float = Field(default=0.0, ge=0.0, le=1.0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
