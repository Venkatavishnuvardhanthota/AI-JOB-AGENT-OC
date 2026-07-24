from __future__ import annotations

from dataclasses import dataclass, field

from app.review.schemas import AutoApprovalCriteria


@dataclass
class ReviewConfig:
    cache_ttl_seconds: int = 300
    strict_validation: bool = True
    track_history: bool = True
    auto_approval_enabled: bool = True
    auto_approval_criteria: AutoApprovalCriteria = field(default_factory=AutoApprovalCriteria)
    max_reviewers: int = 5
    review_expiry_hours: int = 168
    allow_override: bool = True
