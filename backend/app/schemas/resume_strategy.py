import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

RESUME_STRATEGY_USE_EXISTING = "use_existing"
RESUME_STRATEGY_TAILOR = "tailor"
RESUME_STRATEGY_GENERATE = "generate"
RESUME_STRATEGY_ASK = "ask"

VALID_RESUME_STRATEGIES = {
    RESUME_STRATEGY_USE_EXISTING,
    RESUME_STRATEGY_TAILOR,
    RESUME_STRATEGY_GENERATE,
    RESUME_STRATEGY_ASK,
}

SAVE_GENERATED_NEVER = "never"
SAVE_GENERATED_SUBMITTED_ONLY = "submitted_only"
SAVE_GENERATED_EVERY = "every"

VALID_SAVE_GENERATED_RESUMES = {
    SAVE_GENERATED_NEVER,
    SAVE_GENERATED_SUBMITTED_ONLY,
    SAVE_GENERATED_EVERY,
}

DEFAULT_RESUME_STRATEGY = RESUME_STRATEGY_TAILOR
DEFAULT_SAVE_GENERATED_RESUMES = SAVE_GENERATED_SUBMITTED_ONLY


class ResumeStrategy(str, Enum):
    use_existing = RESUME_STRATEGY_USE_EXISTING
    tailor = RESUME_STRATEGY_TAILOR
    generate = RESUME_STRATEGY_GENERATE
    ask = RESUME_STRATEGY_ASK


class SaveGeneratedResumes(str, Enum):
    never = SAVE_GENERATED_NEVER
    submitted_only = SAVE_GENERATED_SUBMITTED_ONLY
    every = SAVE_GENERATED_EVERY


class ResumeStrategySettings(BaseModel):
    resume_strategy: ResumeStrategy
    save_generated_resumes: SaveGeneratedResumes


class ResumeStrategySettingsUpdate(BaseModel):
    resume_strategy: ResumeStrategy | None = None
    save_generated_resumes: SaveGeneratedResumes | None = None


class ResumeSelectionScore(BaseModel):
    resume_id: uuid.UUID
    title: str | None
    skill_overlap: float = Field(ge=0.0, le=1.0)
    keyword_overlap: float = Field(ge=0.0, le=1.0)
    role_alignment: float = Field(ge=0.0, le=1.0)
    ats_compatibility: float = Field(ge=0.0, le=1.0)
    overall: float = Field(ge=0.0, le=1.0)
    selected: bool = False


class ResumeSelectionResult(BaseModel):
    job_id: uuid.UUID
    selected_resume_id: uuid.UUID | None
    selected_title: str | None
    scores: list[ResumeSelectionScore]
    rationale: str


class ResumeStrategyPreview(BaseModel):
    strategy: ResumeStrategy
    resume_id: uuid.UUID | None
    resume_title: str | None
    generated_resume_id: uuid.UUID | None
    generated_resume_title: str | None
    cover_letter_id: uuid.UUID | None
    reused: bool = False


class ResumeStrategyPreviewRequest(BaseModel):
    job_id: uuid.UUID
    resume_id: uuid.UUID | None = None


class ResumeStrategyPreviewResponse(BaseModel):
    recommended_strategy: ResumeStrategy
    selected_resume_id: uuid.UUID | None
    selected_resume_title: str | None
    scores: list[ResumeSelectionScore]
    generated_resume_id: uuid.UUID | None
    generated_resume_title: str | None
    reused_generated: bool = False
    rationale: str


class ResumeStrategyPrepareRequest(BaseModel):
    job_id: uuid.UUID
    strategy_override: ResumeStrategy | None = None
    resume_id: uuid.UUID | None = None
    generate_cover_letter: bool = True


class ResumeStrategyPrepareResponse(BaseModel):
    application_id: uuid.UUID | None
    status: str | None
    needs_choice: bool = False
    strategy: ResumeStrategy
    selected_resume_id: uuid.UUID | None
    selected_resume_title: str | None
    generated_resume_id: uuid.UUID | None
    generated_resume_title: str | None
    cover_letter_id: uuid.UUID | None
    reused_generated: bool = False
    reason: str | None = None
    created_at: datetime | None = None
