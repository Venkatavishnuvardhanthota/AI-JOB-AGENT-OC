from __future__ import annotations

from datetime import datetime
from typing import Any

from app.review.config import ReviewConfig
from app.review.exceptions import AutoApprovalFailedError
from app.review.schemas import (
    AutoApprovalCriteria,
    ReviewDecision,
    ReviewRecord,
    ReviewState,
)
from app.review.validator import ReviewValidator


class DecisionEngine:
    def __init__(
        self,
        validator: ReviewValidator,
        config: ReviewConfig | None = None,
    ) -> None:
        self._validator = validator
        self._config = config or ReviewConfig()

    def approve(
        self,
        record: ReviewRecord,
        reviewer: str | None = None,
        reason: str | None = None,
        comments: str | None = None,
    ) -> ReviewRecord:
        self._validator.validate_state_for_decision(
            record,
            [
                ReviewState.PENDING_REVIEW,
                ReviewState.UNDER_REVIEW,
                ReviewState.CHANGES_REQUESTED,
            ],
        )
        self._validator.validate_expired(record)

        if reviewer:
            self._validator.validate_reviewer(reviewer)
            record.state = ReviewState.UNDER_REVIEW

        self.apply_decision(
            record,
            ReviewDecision.APPROVE,
            ReviewState.APPROVED,
            reviewer or "system",
            reason,
            comments,
        )
        return record

    def reject(
        self,
        record: ReviewRecord,
        reviewer: str,
        reason: str,
        comments: str | None = None,
    ) -> ReviewRecord:
        self._validator.validate_state_for_decision(
            record,
            [
                ReviewState.PENDING_REVIEW,
                ReviewState.UNDER_REVIEW,
                ReviewState.CHANGES_REQUESTED,
            ],
        )
        self._validator.validate_expired(record)
        self._validator.validate_reviewer(reviewer)

        self.apply_decision(
            record,
            ReviewDecision.REJECT,
            ReviewState.REJECTED,
            reviewer,
            reason,
            comments,
        )
        return record

    def request_changes(
        self,
        record: ReviewRecord,
        reviewer: str,
        reason: str,
        comments: str | None = None,
    ) -> ReviewRecord:
        self._validator.validate_state_for_decision(
            record,
            [ReviewState.PENDING_REVIEW, ReviewState.UNDER_REVIEW],
        )
        self._validator.validate_expired(record)
        self._validator.validate_reviewer(reviewer)

        self.apply_decision(
            record,
            ReviewDecision.REQUEST_CHANGES,
            ReviewState.CHANGES_REQUESTED,
            reviewer,
            reason,
            comments,
        )
        return record

    def expire(
        self,
        record: ReviewRecord,
        reason: str | None = None,
    ) -> ReviewRecord:
        self._validator.validate_state_for_decision(
            record,
            [ReviewState.PENDING_REVIEW, ReviewState.UNDER_REVIEW],
        )

        self.apply_decision(
            record,
            ReviewDecision.EXPIRE,
            ReviewState.EXPIRED,
            "system",
            reason or "Review expired.",
        )
        return record

    def auto_approve(
        self,
        record: ReviewRecord,
        match_score: float | None = None,
        ats_score: int | None = None,
        completeness: int | None = None,
        has_match_result: bool = False,
        has_resume: bool = False,
        has_cover_letter: bool = False,
    ) -> ReviewRecord:
        criteria = self._config.auto_approval_criteria
        failures = self._check_criteria(
            criteria,
            match_score,
            ats_score,
            completeness,
            has_match_result,
            has_resume,
            has_cover_letter,
        )

        if failures:
            raise AutoApprovalFailedError(message=f"Auto-approval criteria not met: {'; '.join(failures)}")

        result = self.apply_decision(
            record,
            ReviewDecision.AUTO_APPROVE,
            ReviewState.AUTO_APPROVED,
            "system",
            "Automatically approved.",
            metadata={
                "match_score": match_score,
                "ats_score": ats_score,
                "completeness": completeness,
            },
        )
        return result

    def override(
        self,
        record: ReviewRecord,
        reviewer: str,
        new_state: ReviewState,
        reason: str,
        comments: str | None = None,
    ) -> ReviewRecord:
        self._validator.validate_state_for_decision(
            record,
            [
                ReviewState.APPROVED,
                ReviewState.REJECTED,
                ReviewState.CHANGES_REQUESTED,
                ReviewState.AUTO_APPROVED,
                ReviewState.EXPIRED,
            ],
        )
        self._validator.validate_reviewer(reviewer)

        self._validator.validate_override(record, self._config.allow_override, reason)

        decision = ReviewDecision.OVERRIDE
        state = new_state
        if new_state not in (ReviewState.APPROVED, ReviewState.PENDING_REVIEW):
            state = ReviewState.PENDING_REVIEW if new_state == ReviewState.UNDER_REVIEW else new_state

        self.apply_decision(
            record,
            decision,
            state,
            reviewer,
            reason,
            comments,
        )
        record.override_reason = reason
        return record

    def apply_decision(
        self,
        record: ReviewRecord,
        decision: ReviewDecision,
        new_state: ReviewState,
        reviewer: str,
        reason: str | None,
        comments: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ReviewRecord:
        history_entry = record.model_copy(deep=True)

        record.history.append(history_entry)
        record.state = new_state
        record.decision = decision
        record.reviewer = reviewer
        record.reason = reason
        record.comments = comments
        record.decided_at = datetime.utcnow()
        record.updated_at = datetime.utcnow()

        return record

    @staticmethod
    def _check_criteria(
        criteria: AutoApprovalCriteria,
        match_score: float | None,
        ats_score: int | None,
        completeness: int | None,
        has_match_result: bool,
        has_resume: bool,
        has_cover_letter: bool,
    ) -> list[str]:
        failures: list[str] = []

        if criteria.require_match_result and not has_match_result:
            failures.append("match_result is required")
        elif criteria.match_score_threshold is not None and (
            match_score is None or match_score < criteria.match_score_threshold
        ):
            failures.append(f"match_score {match_score} < threshold {criteria.match_score_threshold}")

        if criteria.require_optimized_resume and not has_resume:
            failures.append("optimized_resume is required")
        elif criteria.ats_score_threshold is not None and (
            ats_score is None or ats_score < criteria.ats_score_threshold
        ):
            failures.append(f"ats_score {ats_score} < threshold {criteria.ats_score_threshold}")

        if criteria.require_cover_letter and not has_cover_letter:
            failures.append("cover_letter is required")

        if criteria.completeness_threshold is not None and (
            completeness is None or completeness < criteria.completeness_threshold
        ):
            failures.append(f"completeness {completeness} < threshold {criteria.completeness_threshold}")

        return failures
