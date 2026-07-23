from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WorkflowState(str, Enum):
    DISCOVERED = "discovered"
    MATCHED = "matched"
    PACKAGE_GENERATED = "package_generated"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    QUEUED = "queued"
    SUBMITTED = "submitted"
    TRACKING = "tracking"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"


class TransitionType(str, Enum):
    TRANSITION = "transition"
    ROLLBACK = "rollback"
    RETRY = "retry"


class HistoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_state: WorkflowState
    to_state: WorkflowState
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: str = "system"
    transition_type: TransitionType = TransitionType.TRANSITION
    reason: str | None = None
    success: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkflowStatus(BaseModel):
    workflow_id: str
    current_state: WorkflowState = WorkflowState.DISCOVERED
    previous_state: WorkflowState | None = None
    history: list[HistoryEntry] = Field(default_factory=list)
    retry_count: int = 0
    locked: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
