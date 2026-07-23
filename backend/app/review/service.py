from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.application_package.schemas import ApplicationPackage
from app.review.cache import ReviewCache
from app.review.config import ReviewConfig
from app.review.exceptions import (
    AutoApprovalFailedError,
    ReviewNotFoundError,
)
from app.review.reviewer import Reviewer
from app.review.schemas import ReviewDecision, ReviewRecord, ReviewState


class ReviewService:
    def __init__(
        self,
        config: ReviewConfig | None = None,
    ) -> None:
        self._config = config or ReviewConfig()
        self._reviewer = Reviewer(self._config)
        self._cache = ReviewCache(self._config)

    def create_review(
        self,
        package_id: str,
        workflow_id: str | None = None,
        tracking_id: str | None = None,
        reviewer: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ReviewRecord:
        existing = self._cache.get(package_id)
        if existing is not None:
            self._reviewer.validator.validate_create(package_id, existing)

        record = self._reviewer.create_review(
            package_id, workflow_id, tracking_id, reviewer, metadata
        )

        if self._config.review_expiry_hours > 0:
            record.expires_at = datetime.utcnow() + timedelta(
                hours=self._config.review_expiry_hours
            )

        self._cache.set(package_id, record)
        return record

    def approve(
        self,
        package_id: str,
        reviewer: str | None = None,
        reason: str | None = None,
        comments: str | None = None,
    ) -> ReviewRecord:
        record = self._get_review(package_id)
        result = self._reviewer.decisions.approve(
            record, reviewer, reason, comments
        )
        self._cache.set(package_id, result)
        return result

    def reject(
        self,
        package_id: str,
        reviewer: str,
        reason: str,
        comments: str | None = None,
    ) -> ReviewRecord:
        record = self._get_review(package_id)
        result = self._reviewer.decisions.reject(
            record, reviewer, reason, comments
        )
        self._cache.set(package_id, result)
        return result

    def request_changes(
        self,
        package_id: str,
        reviewer: str,
        reason: str,
        comments: str | None = None,
    ) -> ReviewRecord:
        record = self._get_review(package_id)
        result = self._reviewer.decisions.request_changes(
            record, reviewer, reason, comments
        )
        self._cache.set(package_id, result)
        return result

    def expire(
        self,
        package_id: str,
        reason: str | None = None,
    ) -> ReviewRecord:
        record = self._get_review(package_id)
        result = self._reviewer.decisions.expire(record, reason)
        self._cache.set(package_id, result)
        return result

    def auto_approve(
        self,
        package_id: str,
        package: ApplicationPackage | None = None,
        match_score: float | None = None,
        ats_score: int | None = None,
        completeness: int | None = None,
        has_match_result: bool = False,
        has_resume: bool = False,
        has_cover_letter: bool = False,
    ) -> ReviewRecord:
        record = self._get_or_create_review(package_id)

        if package:
            completeness = package.completeness_score
            has_match_result = package.match_result is not None
            has_resume = package.resume is not None
            has_cover_letter = package.cover_letter is not None

        try:
            result = self._reviewer.decisions.auto_approve(
                record,
                match_score=match_score,
                ats_score=ats_score,
                completeness=completeness,
                has_match_result=has_match_result,
                has_resume=has_resume,
                has_cover_letter=has_cover_letter,
            )
        except AutoApprovalFailedError:
            result = self._reviewer.decisions._apply_decision(
                record,
                ReviewDecision.APPROVE,
                ReviewState.APPROVED,
                "system",
                "Requires manual review.",
            )

        self._cache.set(package_id, result)
        return result

    def override(
        self,
        package_id: str,
        reviewer: str,
        new_state: ReviewState,
        reason: str,
        comments: str | None = None,
    ) -> ReviewRecord:
        record = self._get_review(package_id)
        result = self._reviewer.decisions.override(
            record, reviewer, new_state, reason, comments
        )
        self._cache.set(package_id, result)
        return result

    def get_review(self, package_id: str) -> ReviewRecord | None:
        return self._cache.get(package_id)

    def get_history(
        self,
        package_id: str,
    ) -> list[ReviewRecord]:
        record = self._cache.get(package_id)
        if record is None:
            return []
        return list(record.history)

    def invalidate_cache(self, package_id: str) -> None:
        self._cache.invalidate(package_id)

    def clear_cache(self) -> None:
        self._cache.clear()

    def _get_review(self, package_id: str) -> ReviewRecord:
        record = self._cache.get(package_id)
        if record is None:
            raise ReviewNotFoundError(
                message=f"No review found for package '{package_id}'."
            )
        return record

    def _get_or_create_review(self, package_id: str) -> ReviewRecord:
        record = self._cache.get(package_id)
        if record is None:
            record = self._reviewer.create_review(package_id)
            self._cache.set(package_id, record)
        return record
