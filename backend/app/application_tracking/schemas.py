from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.workflow.schemas import WorkflowState


class ApplicationStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    QUEUED = "queued"
    SUBMITTED = "submitted"
    VIEWED = "viewed"
    IN_REVIEW = "in_review"
    ASSESSMENT = "assessment"
    INTERVIEW = "interview"
    OFFER = "offer"
    HIRED = "hired"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    ARCHIVED = "archived"


class TimelineEventType(str, Enum):
    APPLICATION_CREATED = "application_created"
    PACKAGE_GENERATED = "package_generated"
    APPROVED = "approved"
    QUEUED = "queued"
    SUBMITTED = "submitted"
    VIEWED = "viewed"
    ASSESSMENT = "assessment"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    ARCHIVED = "archived"
    STATUS_CHANGED = "status_changed"
    WORKFLOW_EVENT = "workflow_event"
    RESTORED = "restored"
    NOTE_ADDED = "note_added"


class TimelineEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: TimelineEventType | str
    actor: str = "system"
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApplicationMetrics(BaseModel):
    days_since_submission: int | None = None
    time_in_current_status_hours: float = 0.0
    total_lifecycle_duration_hours: float = 0.0
    number_of_interviews: int = 0
    retry_count: int = 0
    status_change_count: int = 0
    offer_count: int = 0
    rejection_count: int = 0
    withdrawal_count: int = 0
    timeline_event_count: int = 0


class ApplicationRecord(BaseModel):
    application_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    package_id: str | None = None
    workflow_id: str | None = None
    job_id: str | None = None
    company_id: str | None = None
    resume_version: str | None = None
    cover_letter_version: str | None = None
    submission_timestamp: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    current_status: ApplicationStatus = ApplicationStatus.DRAFT
    workflow_state: WorkflowState | None = None
    priority: int = Field(default=0, ge=0, le=100)
    source_provider: str | None = None
    timeline: list[TimelineEvent] = Field(default_factory=list)
    metrics: ApplicationMetrics = Field(default_factory=ApplicationMetrics)
    metadata: dict[str, Any] = Field(default_factory=dict)
    archived: bool = False
    archived_at: datetime | None = None
    deleted: bool = False
