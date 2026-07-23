from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SubmissionState(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SubmissionPriority(int, Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class StrategyType(str, Enum):
    MANUAL = "manual"
    PLAYWRIGHT = "playwright"
    API_PROVIDER = "api_provider"
    ATS = "ats"


class RetryRecord(BaseModel):
    attempt: int = 0
    max_retries: int = 3
    retry_delay_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    last_attempt_at: datetime | None = None
    next_retry_at: datetime | None = None
    errors: list[str] = Field(default_factory=list)
    non_retryable: bool = False


class SubmissionRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    package_id: str
    workflow_id: str | None = None
    tracking_id: str | None = None
    review_id: str | None = None
    state: SubmissionState = SubmissionState.PENDING
    priority: SubmissionPriority = SubmissionPriority.MEDIUM
    strategy: StrategyType = StrategyType.MANUAL
    dry_run: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_at: datetime | None = None
    dispatched_at: datetime | None = None
    completed_at: datetime | None = None
    failed_at: datetime | None = None
    retry: RetryRecord = Field(default_factory=RetryRecord)
    metadata: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class QueueItem(BaseModel):
    submission_id: str
    priority: SubmissionPriority = SubmissionPriority.MEDIUM
    enqueued_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_at: datetime | None = None


class QueueStatistics(BaseModel):
    total: int = 0
    by_priority: dict[str, int] = Field(default_factory=dict)
    by_state: dict[str, int] = Field(default_factory=dict)
    oldest_enqueued: datetime | None = None
