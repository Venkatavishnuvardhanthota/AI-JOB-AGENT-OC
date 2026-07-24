from __future__ import annotations

from datetime import datetime

from app.review.exceptions import (
    DuplicateReviewError,
    ExpiredReviewError,
    InvalidReviewerError,
    InvalidReviewStateError,
    OverrideNotAllowedError,
    ReviewNotFoundError,
)
from app.review.schemas import ReviewDecision, ReviewRecord, ReviewState


class ReviewValidator:
    def __init__(self, strict: bool = True) -> None:
        self._strict = strict

    def validate_create(
        self,
        package_id: str,
        existing: ReviewRecord | None,
    ) -> None:
        if existing is not None:
            raise DuplicateReviewError(message=f"Review already exists for package '{package_id}'.")

    def validate_get(self, record: ReviewRecord | None) -> ReviewRecord:
        if record is None:
            raise ReviewNotFoundError(message="Review record not found.")
        return record

    def validate_reviewer(self, reviewer: str | None) -> None:
        if self._strict and not reviewer:
            raise InvalidReviewerError(message="A reviewer must be specified for manual review.")

    def validate_expired(self, record: ReviewRecord) -> None:
        if record.expires_at and datetime.utcnow() > record.expires_at:
            raise ExpiredReviewError(message=f"Review '{record.id}' expired at {record.expires_at}.")

    def validate_state_for_decision(
        self,
        record: ReviewRecord,
        allowed_states: list[ReviewState],
    ) -> None:
        if record.state not in allowed_states:
            raise InvalidReviewStateError(
                message=f"Cannot act on review in state '{record.state.value}'. "
                f"Allowed states: {[s.value for s in allowed_states]}"
            )

    def validate_override(
        self,
        record: ReviewRecord,
        override_allowed: bool,
        reason: str | None = None,
    ) -> None:
        if not override_allowed:
            raise OverrideNotAllowedError(message="Override is not enabled for this review.")
        if self._strict and not (reason or record.override_reason):
            raise OverrideNotAllowedError(message="Override reason is required for overrides.")

    def validate_auto_approval_prerequisites(
        self,
        match_result_exists: bool,
        resume_exists: bool,
        cover_letter_exists: bool,
        require_match: bool,
        require_resume: bool,
        require_cover_letter: bool,
    ) -> list[str]:
        missing: list[str] = []
        if require_match and not match_result_exists:
            missing.append("match_result")
        if require_resume and not resume_exists:
            missing.append("optimized_resume")
        if require_cover_letter and not cover_letter_exists:
            missing.append("cover_letter")
        return missing

    @staticmethod
    def get_allowed_decisions(state: ReviewState) -> list[ReviewDecision]:
        mapping: dict[ReviewState, list[ReviewDecision]] = {
            ReviewState.PENDING_REVIEW: [
                ReviewDecision.APPROVE,
                ReviewDecision.REJECT,
                ReviewDecision.REQUEST_CHANGES,
                ReviewDecision.AUTO_APPROVE,
                ReviewDecision.EXPIRE,
            ],
            ReviewState.UNDER_REVIEW: [
                ReviewDecision.APPROVE,
                ReviewDecision.REJECT,
                ReviewDecision.REQUEST_CHANGES,
            ],
            ReviewState.APPROVED: [ReviewDecision.OVERRIDE],
            ReviewState.REJECTED: [ReviewDecision.OVERRIDE],
            ReviewState.CHANGES_REQUESTED: [
                ReviewDecision.APPROVE,
                ReviewDecision.REJECT,
                ReviewDecision.OVERRIDE,
            ],
            ReviewState.AUTO_APPROVED: [ReviewDecision.OVERRIDE],
            ReviewState.EXPIRED: [ReviewDecision.OVERRIDE],
        }
        return mapping.get(state, [])
