from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class TraceEntry(BaseModel):
    span_id: str
    trace_id: str
    parent_id: str | None = None
    name: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: datetime | None = None
    duration_ms: float | None = None
    tags: dict[str, Any] = Field(default_factory=dict)


class MetricPoint(BaseModel):
    name: str
    value: float
    tags: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthCheckResult(BaseModel):
    component: str
    status: HealthStatus
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=datetime.utcnow)


class DiagnosticFinding(BaseModel):
    finding_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    severity: str
    category: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    detected_at: datetime = Field(default_factory=datetime.utcnow)


class HistoryEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    orchestration_id: str
    event_type: str
    state: str
    duration_ms: float | None = None
    error: str | None = None
    warnings: list[str] = Field(default_factory=list)
    resume_count: int = 0
    retry_count: int = 0
    manual_intervention_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    orchestration_id: str
    state: str
    execution_mode: str
    total_duration_ms: float | None = None
    stages_completed: int = 0
    stages_failed: int = 0
    stages_skipped: int = 0
    retry_count: int = 0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class PerformanceReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    period_start: datetime
    period_end: datetime
    total_orchestrations: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_duration_ms: float | None = None
    p95_duration_ms: float | None = None
    top_slow_stages: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ProviderReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: str
    total_requests: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_latency_ms: float | None = None
    error_rate: float | None = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class UsageReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    total_ai_requests: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    model_breakdown: dict[str, dict[str, Any]] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class FailureReport(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    total_failures: int = 0
    failures_by_stage: dict[str, int] = Field(default_factory=dict)
    failures_by_error: dict[str, int] = Field(default_factory=dict)
    top_failures: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class SystemSummary(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    uptime_hours: float = 0.0
    total_orchestrations: int = 0
    active_orchestrations: int = 0
    total_ai_requests: int = 0
    total_browser_actions: int = 0
    total_uploads: int = 0
    total_submissions: int = 0
    error_rate: float | None = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
