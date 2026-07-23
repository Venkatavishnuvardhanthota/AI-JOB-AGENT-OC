from __future__ import annotations

from typing import Any

from app.review.config import ReviewConfig
from app.review.decision import DecisionEngine
from app.review.schemas import (
    ReviewRecord,
    ReviewState,
)
from app.review.validator import ReviewValidator


class Reviewer:
    def __init__(
        self,
        config: ReviewConfig | None = None,
    ) -> None:
        self._config = config or ReviewConfig()
        self._validator = ReviewValidator(strict=self._config.strict_validation)
        self._decisions = DecisionEngine(self._validator, self._config)

    def create_review(
        self,
        package_id: str,
        workflow_id: str | None = None,
        tracking_id: str | None = None,
        reviewer: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ReviewRecord:
        record = ReviewRecord(
            package_id=package_id,
            workflow_id=workflow_id,
            tracking_id=tracking_id,
            reviewer=reviewer,
            metadata=metadata or {},
            state=ReviewState.PENDING_REVIEW,
        )

        if reviewer:
            self._validator.validate_reviewer(reviewer)

        return record

    def update_review(
        self,
        record: ReviewRecord,
        reviewer: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ReviewRecord:
        if reviewer:
            record.reviewer = reviewer
            if record.state == ReviewState.PENDING_REVIEW:
                record.state = ReviewState.UNDER_REVIEW
        if metadata:
            record.metadata.update(metadata)
        record.updated_at = __import__("datetime").datetime.utcnow()
        return record

    @property
    def decisions(self) -> DecisionEngine:
        return self._decisions

    @property
    def validator(self) -> ReviewValidator:
        return self._validator
