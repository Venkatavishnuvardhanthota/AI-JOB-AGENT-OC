from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ReviewState(str, Enum):
    PENDING_REVIEW = "pending_review"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"
    AUTO_APPROVED = "auto_approved"
    EXPIRED = "expired"


class ReviewDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    AUTO_APPROVE = "auto_approve"
    EXPIRE = "expire"
    OVERRIDE = "override"


class ReviewRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    package_id: str
    workflow_id: str | None = None
    tracking_id: str | None = None
    state: ReviewState = ReviewState.PENDING_REVIEW
    decision: ReviewDecision | None = None
    reviewer: str | None = None
    reason: str | None = None
    comments: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    decided_at: datetime | None = None
    auto_approval_criteria: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    history: list[ReviewRecord] = Field(default_factory=list)
    override_reason: str | None = None
    expires_at: datetime | None = None


class AutoApprovalCriteria(BaseModel):
    match_score_threshold: float | None = None
    ats_score_threshold: int | None = None
    completeness_threshold: int | None = None
    require_match_result: bool = True
    require_optimized_resume: bool = True
    require_cover_letter: bool = True
