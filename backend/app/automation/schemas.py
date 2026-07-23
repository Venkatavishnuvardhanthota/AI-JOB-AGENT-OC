from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AutomationType(str, Enum):
    MANUAL = "manual"
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    EVENT_DRIVEN = "event_driven"


class TriggerType(str, Enum):
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CRON = "cron"
    WORKFLOW_EVENT = "workflow_event"
    REVIEW_APPROVAL = "review_approval"
    SUBMISSION_COMPLETION = "submission_completion"
    MANUAL = "manual"


class JobPriority(int, Enum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class JobState(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRIED = "retried"
    SKIPPED = "skipped"


class AutomationTrigger(BaseModel):
    trigger_type: TriggerType = TriggerType.MANUAL
    scheduled_at: datetime | None = None
    cron_expression: str | None = None
    daily_time: str | None = None
    weekly_day: int | None = None
    weekly_time: str | None = None
    monthly_day: int | None = None
    monthly_time: str | None = None
    event_source: str | None = None
    event_type: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class AutomationPolicy(BaseModel):
    auto_search_jobs: bool = False
    auto_generate_packages: bool = False
    require_review: bool = True
    auto_approve_threshold: float | None = None
    auto_submit_only_when_approved: bool = True
    max_concurrent_jobs: int = 5
    max_retries: int = 3
    execution_timeout_seconds: float = 3600.0
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    rate_limit_per_minute: int = 10
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AutomationJob(BaseModel):
    id: str
    name: str
    description: str = ""
    enabled: bool = True
    priority: JobPriority = JobPriority.MEDIUM
    automation_type: AutomationType = AutomationType.MANUAL
    trigger: AutomationTrigger = Field(default_factory=AutomationTrigger)
    policy: AutomationPolicy = Field(default_factory=AutomationPolicy)
    target_module: str
    target_action: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    retry_count: int = 0
    state: JobState = JobState.ACTIVE
    metadata: dict[str, Any] = Field(default_factory=dict)


class QueueItem(BaseModel):
    job_id: str
    priority: JobPriority = JobPriority.MEDIUM
    enqueued_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_at: datetime | None = None


class QueueStatistics(BaseModel):
    total: int = 0
    by_priority: dict[str, int] = Field(default_factory=dict)
    by_state: dict[str, int] = Field(default_factory=dict)
    oldest_enqueued: datetime | None = None
    paused: bool = False


class HistoryQuery(BaseModel):
    job_id: str | None = None
    status: ExecutionStatus | None = None
    limit: int = 50
    offset: int = 0
