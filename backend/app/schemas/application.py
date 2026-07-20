import uuid
from datetime import datetime

from pydantic import BaseModel


class ApplicationPrepareRequest(BaseModel):
    job_id: uuid.UUID
    resume_id: uuid.UUID
    generate_cover_letter: bool = True
    generate_ai_answers: bool = True


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    resume_id: uuid.UUID | None
    cover_letter_id: uuid.UUID | None
    status: str
    notes: str | None
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    id: uuid.UUID
    job_title: str | None
    company: str | None
    status: str
    submitted_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationSubmitResponse(BaseModel):
    status: str
    submitted_at: datetime


class ApplicationTimelineEntry(BaseModel):
    event: str
    timestamp: datetime


class CoverLetterGenerateRequest(BaseModel):
    template: str = "professional"


class AnswerGenerateRequest(BaseModel):
    questions: list[str]


class AnswerResponse(BaseModel):
    question: str
    answer: str
    approved: bool = False
