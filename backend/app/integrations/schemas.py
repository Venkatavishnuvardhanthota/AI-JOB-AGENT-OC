from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    JOB_DISCOVERED = "job_discovered"
    JOB_MATCHED = "job_matched"
    APPLICATION_PREPARED = "application_prepared"
    APPLICATION_SUBMITTED = "application_submitted"
    APPLICATION_FAILED = "application_failed"
    APPLICATION_ACCEPTED = "application_accepted"
    APPLICATION_REJECTED = "application_rejected"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    MANUAL_INTERVENTION_REQUIRED = "manual_intervention_required"
    ORCHESTRATION_PAUSED = "orchestration_paused"
    ORCHESTRATION_RESUMED = "orchestration_resumed"
    REPORT_GENERATED = "report_generated"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_ERROR = "system_error"
    CUSTOM = "custom"


class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class DeliveryChannel(str, Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    TEAMS = "teams"
    BROWSER = "browser"
    DESKTOP = "desktop"
    CONSOLE = "console"


class ProviderStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


class NotificationMessage(BaseModel):
    type: NotificationType
    title: str
    body: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    recipient: str | None = None
    channel: DeliveryChannel | None = None
    template_name: str | None = None
    template_variables: dict[str, str] = Field(default_factory=dict)
    attachments: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    provider: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProviderMetadata(BaseModel):
    name: str
    display_name: str
    description: str = ""
    version: str = "0.1.0"
    channel: DeliveryChannel
    supports_templates: bool = False
    supports_attachments: bool = False
    supports_priority: bool = False
    configurable: dict[str, Any] = Field(default_factory=dict)


class ProviderHealth(BaseModel):
    status: ProviderStatus = ProviderStatus.UNHEALTHY
    message: str = ""
    last_check: datetime = Field(default_factory=datetime.utcnow)
    response_time_ms: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class DeliveryRecord(BaseModel):
    id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex[:12])
    message: NotificationMessage
    provider: str
    channel: DeliveryChannel
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    last_attempt: datetime | None = None
    next_retry: datetime | None = None
    error: str | None = None
    delivered_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationTemplate(BaseModel):
    name: str
    subject_template: str = ""
    body_template: str
    html_template: str | None = None
    channel: DeliveryChannel | None = None
    variables: list[str] = Field(default_factory=list)


class EmailMessage(BaseModel):
    to: list[str]
    subject: str
    body: str
    html_body: str | None = None
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    reply_to: str | None = None
    attachments: list[str] = Field(default_factory=list)
    priority: NotificationPriority = NotificationPriority.NORMAL


class WebhookPayload(BaseModel):
    url: str
    method: str = "POST"
    headers: dict[str, str] = Field(default_factory=dict)
    body: dict[str, Any] = Field(default_factory=dict)
    hmac_secret: str | None = None
    hmac_header: str = "X-Signature-256"


class RichMessage(BaseModel):
    title: str
    description: str = ""
    status: str | None = None
    color: str | None = None
    fields: list[dict[str, str]] = Field(default_factory=list)
    footer: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    links: dict[str, str] = Field(default_factory=dict)
    provider_name: str | None = None
    orchestration_id: str | None = None
    application_id: str | None = None
    errors: list[str] = Field(default_factory=list)
