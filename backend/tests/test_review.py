from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest

from app.review.cache import ReviewCache
from app.review.config import ReviewConfig
from app.review.decision import DecisionEngine
from app.review.exceptions import (
    AutoApprovalFailedError,
    DuplicateReviewError,
    ExpiredReviewError,
    InvalidReviewerError,
    InvalidReviewStateError,
    OverrideNotAllowedError,
    ReviewNotFoundError,
)
from app.review.history import ReviewHistory
from app.review.reviewer import Reviewer
from app.review.schemas import (
    AutoApprovalCriteria,
    ReviewDecision,
    ReviewRecord,
    ReviewState,
)
from app.review.service import ReviewService
from app.review.validator import ReviewValidator


class TestReviewState:
    def test_all_states_defined(self):
        expected = [
            "pending_review", "under_review", "approved", "rejected",
            "changes_requested", "auto_approved", "expired",
        ]
        values = [s.value for s in ReviewState]
        for exp in expected:
            assert exp in values

    def test_all_states_unique(self):
        values = [s.value for s in ReviewState]
        assert len(values) == len(set(values))


class TestReviewConfig:
    def test_default_config(self):
        config = ReviewConfig()
        assert config.cache_ttl_seconds == 300
        assert config.strict_validation is True
        assert config.auto_approval_enabled is True
        assert config.max_reviewers == 5
        assert config.review_expiry_hours == 168
        assert config.allow_override is True

    def test_custom_config(self):
        config = ReviewConfig(
            cache_ttl_seconds=600,
            strict_validation=False,
            auto_approval_enabled=False,
            max_reviewers=3,
            review_expiry_hours=72,
            allow_override=False,
        )
        assert config.cache_ttl_seconds == 600
        assert config.strict_validation is False
        assert config.max_reviewers == 3
        assert config.review_expiry_hours == 72
        assert config.allow_override is False


class TestReviewValidator:
    def test_validate_create_new(self):
        validator = ReviewValidator()
        validator.validate_create("pkg-1", None)

    def test_validate_create_duplicate(self):
        validator = ReviewValidator()
        existing = ReviewRecord(package_id="pkg-1")
        with pytest.raises(DuplicateReviewError):
            validator.validate_create("pkg-1", existing)

    def test_validate_get_exists(self):
        validator = ReviewValidator()
        record = ReviewRecord(package_id="test")
        result = validator.validate_get(record)
        assert result.package_id == "test"

    def test_validate_get_none(self):
        validator = ReviewValidator()
        with pytest.raises(ReviewNotFoundError):
            validator.validate_get(None)

    def test_validate_reviewer_valid(self):
        validator = ReviewValidator()
        validator.validate_reviewer("user-1")

    def test_validate_reviewer_none_strict(self):
        validator = ReviewValidator()
        with pytest.raises(InvalidReviewerError):
            validator.validate_reviewer(None)

    def test_validate_reviewer_none_not_strict(self):
        validator = ReviewValidator(strict=False)
        validator.validate_reviewer(None)

    def test_validate_expired_not_expired(self):
        validator = ReviewValidator()
        record = ReviewRecord(
            package_id="test",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        validator.validate_expired(record)

    def test_validate_expired(self):
        validator = ReviewValidator()
        record = ReviewRecord(
            package_id="test",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        with pytest.raises(ExpiredReviewError):
            validator.validate_expired(record)

    def test_validate_expired_no_expiry(self):
        validator = ReviewValidator()
        record = ReviewRecord(package_id="test", expires_at=None)
        validator.validate_expired(record)

    def test_validate_state_for_decision_allowed(self):
        validator = ReviewValidator()
        record = ReviewRecord(package_id="test", state=ReviewState.PENDING_REVIEW)
        validator.validate_state_for_decision(
            record, [ReviewState.PENDING_REVIEW, ReviewState.UNDER_REVIEW]
        )

    def test_validate_state_for_decision_not_allowed(self):
        validator = ReviewValidator()
        record = ReviewRecord(package_id="test", state=ReviewState.APPROVED)
        with pytest.raises(InvalidReviewStateError):
            validator.validate_state_for_decision(
                record, [ReviewState.PENDING_REVIEW]
            )

    def test_validate_override_allowed(self):
        validator = ReviewValidator()
        record = ReviewRecord(
            package_id="test", override_reason="Need to revert"
        )
        validator.validate_override(record, override_allowed=True)

    def test_validate_override_not_allowed(self):
        validator = ReviewValidator()
        record = ReviewRecord(package_id="test")
        with pytest.raises(OverrideNotAllowedError):
            validator.validate_override(record, override_allowed=False)

    def test_validate_override_no_reason_strict(self):
        validator = ReviewValidator()
        record = ReviewRecord(package_id="test")
        with pytest.raises(OverrideNotAllowedError):
            validator.validate_override(record, override_allowed=True)

    def test_validate_auto_approval_prerequisites_all_met(self):
        validator = ReviewValidator()
        missing = validator.validate_auto_approval_prerequisites(
            True, True, True, True, True, True
        )
        assert missing == []

    def test_validate_auto_approval_prerequisites_missing(self):
        validator = ReviewValidator()
        missing = validator.validate_auto_approval_prerequisites(
            False, False, False, True, True, True
        )
        assert len(missing) == 3

    def test_get_allowed_decisions_pending(self):
        allowed = ReviewValidator.get_allowed_decisions(ReviewState.PENDING_REVIEW)
        assert ReviewDecision.APPROVE in allowed
        assert ReviewDecision.REJECT in allowed
        assert ReviewDecision.REQUEST_CHANGES in allowed
        assert ReviewDecision.EXPIRE in allowed

    def test_get_allowed_decisions_approved(self):
        allowed = ReviewValidator.get_allowed_decisions(ReviewState.APPROVED)
        assert allowed == [ReviewDecision.OVERRIDE]

    def test_get_allowed_decisions_auto_approved(self):
        allowed = ReviewValidator.get_allowed_decisions(ReviewState.AUTO_APPROVED)
        assert allowed == [ReviewDecision.OVERRIDE]

    def test_get_allowed_decisions_expired(self):
        allowed = ReviewValidator.get_allowed_decisions(ReviewState.EXPIRED)
        assert allowed == [ReviewDecision.OVERRIDE]


class TestDecisionEngine:
    def test_approve(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test")
        result = engine.approve(record, reviewer="user-1", reason="Looks good")
        assert result.state == ReviewState.APPROVED
        assert result.decision == ReviewDecision.APPROVE
        assert result.reviewer == "user-1"
        assert result.reason == "Looks good"
        assert result.decided_at is not None

    def test_approve_without_reviewer_system(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test")
        result = engine.approve(record, reason="Auto OK")
        assert result.state == ReviewState.APPROVED
        assert result.reviewer == "system"

    def test_approve_from_changes_requested(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(
            package_id="test", state=ReviewState.CHANGES_REQUESTED
        )
        result = engine.approve(record, reviewer="user-1", reason="Changes addressed")
        assert result.state == ReviewState.APPROVED

    def test_approve_expired_review(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(
            package_id="test",
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        with pytest.raises(ExpiredReviewError):
            engine.approve(record, reviewer="user-1", reason="Late")

    def test_reject(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test")
        result = engine.reject(
            record, reviewer="user-1", reason="Missing required docs"
        )
        assert result.state == ReviewState.REJECTED
        assert result.decision == ReviewDecision.REJECT
        assert result.reviewer == "user-1"

    def test_reject_no_reviewer(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test")
        with pytest.raises(InvalidReviewerError):
            engine.reject(record, reviewer=None, reason="Bad")

    def test_reject_no_reason(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test")
        result = engine.reject(record, reviewer="user-1", reason="No reason")
        assert result.state == ReviewState.REJECTED

    def test_request_changes(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test")
        result = engine.request_changes(
            record, reviewer="user-1", reason="Fix formatting"
        )
        assert result.state == ReviewState.CHANGES_REQUESTED
        assert result.decision == ReviewDecision.REQUEST_CHANGES

    def test_request_changes_from_approved_fails(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test", state=ReviewState.APPROVED)
        with pytest.raises(InvalidReviewStateError):
            engine.request_changes(record, reviewer="user-1", reason="Oops")

    def test_expire(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test")
        result = engine.expire(record, reason="Timed out")
        assert result.state == ReviewState.EXPIRED
        assert result.decision == ReviewDecision.EXPIRE

    def test_expire_from_approved_fails(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test", state=ReviewState.APPROVED)
        with pytest.raises(InvalidReviewStateError):
            engine.expire(record)

    def test_auto_approve_meets_criteria(self):
        config = ReviewConfig(
            auto_approval_criteria=AutoApprovalCriteria(
                match_score_threshold=70.0,
                ats_score_threshold=80,
                completeness_threshold=90,
                require_match_result=True,
                require_optimized_resume=True,
                require_cover_letter=True,
            )
        )
        validator = ReviewValidator()
        engine = DecisionEngine(validator, config)
        record = ReviewRecord(package_id="test")
        result = engine.auto_approve(
            record,
            match_score=85.0,
            ats_score=90,
            completeness=95,
            has_match_result=True,
            has_resume=True,
            has_cover_letter=True,
        )
        assert result.state == ReviewState.AUTO_APPROVED
        assert result.decision == ReviewDecision.AUTO_APPROVE

    def test_auto_approve_fails_low_match_score(self):
        config = ReviewConfig(
            auto_approval_criteria=AutoApprovalCriteria(
                match_score_threshold=70.0,
            )
        )
        validator = ReviewValidator()
        engine = DecisionEngine(validator, config)
        record = ReviewRecord(package_id="test")
        with pytest.raises(AutoApprovalFailedError):
            engine.auto_approve(
                record,
                match_score=50.0,
                has_match_result=True,
            )

    def test_auto_approve_fails_low_ats_score(self):
        config = ReviewConfig(
            auto_approval_criteria=AutoApprovalCriteria(
                ats_score_threshold=80,
            )
        )
        validator = ReviewValidator()
        engine = DecisionEngine(validator, config)
        record = ReviewRecord(package_id="test")
        with pytest.raises(AutoApprovalFailedError):
            engine.auto_approve(
                record,
                ats_score=60,
                has_resume=True,
            )

    def test_auto_approve_fails_low_completeness(self):
        config = ReviewConfig(
            auto_approval_criteria=AutoApprovalCriteria(
                completeness_threshold=90,
            )
        )
        validator = ReviewValidator()
        engine = DecisionEngine(validator, config)
        record = ReviewRecord(package_id="test")
        with pytest.raises(AutoApprovalFailedError):
            engine.auto_approve(record, completeness=50)

    def test_auto_approve_fails_missing_docs(self):
        config = ReviewConfig(
            auto_approval_criteria=AutoApprovalCriteria(
                require_match_result=True,
                require_optimized_resume=True,
                require_cover_letter=True,
            )
        )
        validator = ReviewValidator()
        engine = DecisionEngine(validator, config)
        record = ReviewRecord(package_id="test")
        with pytest.raises(AutoApprovalFailedError):
            engine.auto_approve(
                record,
                has_match_result=False,
                has_resume=False,
                has_cover_letter=False,
            )

    def test_override_approved_to_pending(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test", state=ReviewState.APPROVED)
        result = engine.override(
            record,
            reviewer="admin-1",
            new_state=ReviewState.PENDING_REVIEW,
            reason="Reopen for review",
        )
        assert result.state == ReviewState.PENDING_REVIEW
        assert result.decision == ReviewDecision.OVERRIDE
        assert result.override_reason == "Reopen for review"

    def test_override_rejected_to_pending(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test", state=ReviewState.REJECTED)
        result = engine.override(
            record,
            reviewer="admin-1",
            new_state=ReviewState.PENDING_REVIEW,
            reason="New information available",
        )
        assert result.state == ReviewState.PENDING_REVIEW

    def test_override_auto_approved_to_pending(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test", state=ReviewState.AUTO_APPROVED)
        result = engine.override(
            record,
            reviewer="admin-1",
            new_state=ReviewState.PENDING_REVIEW,
            reason="Manual review needed after all",
        )
        assert result.state == ReviewState.PENDING_REVIEW

    def test_override_not_allowed_config(self):
        config = ReviewConfig(allow_override=False)
        validator = ReviewValidator()
        engine = DecisionEngine(validator, config)
        record = ReviewRecord(package_id="test", state=ReviewState.APPROVED)
        with pytest.raises(OverrideNotAllowedError):
            engine.override(
                record,
                reviewer="admin-1",
                new_state=ReviewState.PENDING_REVIEW,
                reason="Override",
            )

    def test_override_without_reason(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test", state=ReviewState.APPROVED)
        with pytest.raises(OverrideNotAllowedError):
            engine.override(
                record,
                reviewer="admin-1",
                new_state=ReviewState.PENDING_REVIEW,
                reason="",
            )

    def test_approve_preserves_history(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test")
        result = engine.approve(record, reviewer="user-1", reason="Good")
        assert len(result.history) == 1
        assert result.state == ReviewState.APPROVED

    def test_reject_preserves_history(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test")
        result = engine.reject(record, reviewer="user-1", reason="Bad")
        assert len(result.history) == 1

    def test_multiple_decisions_accumulate_history(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test")
        record = engine.approve(record, reviewer="user-1", reason="First")
        assert len(record.history) == 1
        record = engine.override(
            record,
            reviewer="admin-1",
            new_state=ReviewState.PENDING_REVIEW,
            reason="Reopen",
        )
        assert len(record.history) == 2

    def test_approve_from_under_review(self):
        validator = ReviewValidator()
        engine = DecisionEngine(validator)
        record = ReviewRecord(package_id="test", state=ReviewState.UNDER_REVIEW)
        result = engine.approve(record, reviewer="user-1", reason="Good")
        assert result.state == ReviewState.APPROVED


class TestReviewer:
    def test_create_review(self):
        reviewer = Reviewer()
        record = reviewer.create_review("pkg-1")
        assert record.package_id == "pkg-1"
        assert record.state == ReviewState.PENDING_REVIEW
        assert record.reviewer is None

    def test_create_review_with_reviewer(self):
        reviewer = Reviewer()
        record = reviewer.create_review("pkg-1", reviewer="user-1")
        assert record.reviewer == "user-1"

    def test_create_review_with_metadata(self):
        reviewer = Reviewer()
        record = reviewer.create_review(
            "pkg-1", metadata={"source": "automated"}
        )
        assert record.metadata["source"] == "automated"

    def test_update_review_sets_reviewer(self):
        reviewer = Reviewer()
        record = reviewer.create_review("pkg-1")
        result = reviewer.update_review(record, reviewer="user-1")
        assert result.reviewer == "user-1"
        assert result.state == ReviewState.UNDER_REVIEW

    def test_update_review_already_under_review(self):
        reviewer = Reviewer()
        record = reviewer.create_review("pkg-1", reviewer="user-1")
        result = reviewer.update_review(record, reviewer="user-2")
        assert result.reviewer == "user-2"
        assert result.state == ReviewState.UNDER_REVIEW

    def test_update_review_with_metadata(self):
        reviewer = Reviewer()
        record = reviewer.create_review("pkg-1")
        result = reviewer.update_review(record, metadata={"key": "value"})
        assert result.metadata["key"] == "value"


class TestReviewHistory:
    def test_add_and_get_history(self):
        history = ReviewHistory()
        entry = ReviewRecord(package_id="pkg-1")
        history.add("rev-1", entry)
        entries = history.get_history("rev-1")
        assert len(entries) == 1

    def test_get_history_empty(self):
        history = ReviewHistory()
        assert history.get_history("nonexistent") == []

    def test_clear_specific(self):
        history = ReviewHistory()
        history.add("r1", ReviewRecord(package_id="p1"))
        history.add("r2", ReviewRecord(package_id="p2"))
        history.clear("r1")
        assert history.count("r1") == 0
        assert history.count("r2") == 1

    def test_clear_all(self):
        history = ReviewHistory()
        history.add("r1", ReviewRecord(package_id="p1"))
        history.add("r2", ReviewRecord(package_id="p2"))
        history.clear()
        assert history.count("r1") == 0
        assert history.count("r2") == 0


class TestReviewCache:
    def test_set_and_get(self):
        config = ReviewConfig(cache_ttl_seconds=300)
        cache = ReviewCache(config)
        record = ReviewRecord(package_id="test")
        cache.set("k1", record)
        result = cache.get("k1")
        assert result is not None
        assert result.package_id == "test"

    def test_get_missing(self):
        config = ReviewConfig()
        cache = ReviewCache(config)
        assert cache.get("nonexistent") is None

    def test_invalidate(self):
        config = ReviewConfig()
        cache = ReviewCache(config)
        cache.set("k1", ReviewRecord(package_id="test"))
        cache.invalidate("k1")
        assert cache.get("k1") is None

    def test_clear(self):
        config = ReviewConfig()
        cache = ReviewCache(config)
        cache.set("k1", ReviewRecord(package_id="t1"))
        cache.set("k2", ReviewRecord(package_id="t2"))
        cache.clear()
        assert cache.get("k1") is None
        assert cache.get("k2") is None

    def test_ttl_expiry(self):
        config = ReviewConfig(cache_ttl_seconds=0)
        cache = ReviewCache(config)
        cache.set("k1", ReviewRecord(package_id="test"))
        import time
        time.sleep(0.01)
        result = cache.get("k1")
        assert result is None

    def test_thread_safety(self):
        config = ReviewConfig()
        cache = ReviewCache(config)
        import threading
        errors = []

        def worker(ident: str):
            try:
                for i in range(100):
                    key = f"{ident}-{i}"
                    cache.set(key, ReviewRecord(package_id=key))
                    cache.get(key)
                    cache.invalidate(key)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(f"t{i}",)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0


class TestReviewService:
    def test_create_review(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        record = service.create_review(pkg_id)
        assert record.package_id == pkg_id
        assert record.state == ReviewState.PENDING_REVIEW

    def test_create_review_with_reviewer(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        record = service.create_review(pkg_id, reviewer="user-1")
        assert record.reviewer == "user-1"

    def test_create_review_sets_expiry(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        record = service.create_review(pkg_id)
        assert record.expires_at is not None

    def test_create_review_no_expiry(self):
        config = ReviewConfig(review_expiry_hours=0)
        service = ReviewService(config)
        pkg_id = str(uuid.uuid4())
        record = service.create_review(pkg_id)
        assert record.expires_at is None

    def test_create_duplicate_review(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        service.create_review(pkg_id)
        with pytest.raises(DuplicateReviewError):
            service.create_review(pkg_id)

    def test_get_review(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        service.create_review(pkg_id)
        record = service.get_review(pkg_id)
        assert record is not None
        assert record.package_id == pkg_id

    def test_get_review_nonexistent(self):
        service = ReviewService()
        assert service.get_review("nonexistent") is None

    def test_approve(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        service.create_review(pkg_id)
        result = service.approve(pkg_id, reviewer="user-1", reason="Good")
        assert result.state == ReviewState.APPROVED

    def test_approve_nonexistent_raises(self):
        service = ReviewService()
        with pytest.raises(ReviewNotFoundError):
            service.approve("nonexistent", reviewer="user-1", reason="Good")

    def test_reject(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        service.create_review(pkg_id)
        result = service.reject(
            pkg_id, reviewer="user-1", reason="Insufficient quality"
        )
        assert result.state == ReviewState.REJECTED

    def test_request_changes(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        service.create_review(pkg_id)
        result = service.request_changes(
            pkg_id, reviewer="user-1", reason="Fix resume formatting"
        )
        assert result.state == ReviewState.CHANGES_REQUESTED

    def test_expire(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        service.create_review(pkg_id)
        result = service.expire(pkg_id, reason="No response")
        assert result.state == ReviewState.EXPIRED

    def test_auto_approve_meets_criteria(self):
        config = ReviewConfig(
            auto_approval_criteria=AutoApprovalCriteria(
                match_score_threshold=70.0,
                completeness_threshold=80,
                require_match_result=True,
                require_optimized_resume=False,
                require_cover_letter=False,
            )
        )
        service = ReviewService(config)
        pkg_id = str(uuid.uuid4())
        result = service.auto_approve(
            pkg_id,
            match_score=85.0,
            completeness=90,
            has_match_result=True,
        )
        assert result.state == ReviewState.AUTO_APPROVED

    def test_auto_approve_falls_back_to_manual(self):
        config = ReviewConfig(
            auto_approval_criteria=AutoApprovalCriteria(
                match_score_threshold=90.0,
            )
        )
        service = ReviewService(config)
        pkg_id = str(uuid.uuid4())
        result = service.auto_approve(
            pkg_id,
            match_score=50.0,
            has_match_result=True,
        )
        assert result.state == ReviewState.APPROVED

    def test_override(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        service.create_review(pkg_id)
        service.approve(pkg_id, reviewer="user-1", reason="Good")
        result = service.override(
            pkg_id,
            reviewer="admin-1",
            new_state=ReviewState.PENDING_REVIEW,
            reason="Reopen for corrections",
        )
        assert result.state == ReviewState.PENDING_REVIEW
        assert result.decision == ReviewDecision.OVERRIDE

    def test_get_history(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        service.create_review(pkg_id)
        service.approve(pkg_id, reviewer="user-1", reason="Good")
        history = service.get_history(pkg_id)
        assert len(history) == 1
        assert history[0].state in (
            ReviewState.PENDING_REVIEW, ReviewState.UNDER_REVIEW
        )

    def test_get_history_nonexistent(self):
        service = ReviewService()
        assert service.get_history("nonexistent") == []

    def test_invalidate_cache(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        service.create_review(pkg_id)
        service.invalidate_cache(pkg_id)
        assert service.get_review(pkg_id) is None

    def test_clear_cache(self):
        service = ReviewService()
        pkg_id1 = str(uuid.uuid4())
        pkg_id2 = str(uuid.uuid4())
        service.create_review(pkg_id1)
        service.create_review(pkg_id2)
        service.clear_cache()
        assert service.get_review(pkg_id1) is None
        assert service.get_review(pkg_id2) is None

    def test_deterministic_behavior(self):
        service = ReviewService()
        pkg1 = str(uuid.uuid4())
        pkg2 = str(uuid.uuid4())
        service.create_review(pkg1)
        service.create_review(pkg2)
        service.approve(pkg1, reviewer="user-1", reason="Good")
        service.approve(pkg2, reviewer="user-1", reason="Good")
        r1 = service.get_review(pkg1)
        r2 = service.get_review(pkg2)
        assert r1 is not None and r2 is not None
        assert r1.state == r2.state
        assert r1.decision == r2.decision

    def test_full_review_lifecycle(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        service.create_review(pkg_id)
        service.approve(pkg_id, reviewer="user-1", reason="Looks good")
        r1 = service.get_review(pkg_id)
        assert r1 is not None
        assert r1.state == ReviewState.APPROVED

        service.override(
            pkg_id,
            reviewer="admin-1",
            new_state=ReviewState.PENDING_REVIEW,
            reason="Need corrections",
        )
        r2 = service.get_review(pkg_id)
        assert r2 is not None
        assert r2.state == ReviewState.PENDING_REVIEW
        assert r2.decision == ReviewDecision.OVERRIDE

        service.approve(pkg_id, reviewer="user-1", reason="Now acceptable")
        r3 = service.get_review(pkg_id)
        assert r3 is not None
        assert r3.state == ReviewState.APPROVED
        assert len(r3.history) == 3


class TestSerialization:
    def test_review_record_serialization(self):
        record = ReviewRecord(
            package_id="pkg-1",
            state=ReviewState.APPROVED,
            decision=ReviewDecision.APPROVE,
        )
        data = record.model_dump()
        assert data["package_id"] == "pkg-1"
        assert data["state"] == "approved"
        assert data["decision"] == "approve"

    def test_review_record_with_history(self):
        entry = ReviewRecord(
            package_id="pkg-1",
            state=ReviewState.PENDING_REVIEW,
        )
        record = ReviewRecord(
            package_id="pkg-1",
            state=ReviewState.APPROVED,
            history=[entry],
        )
        data = record.model_dump()
        assert len(data["history"]) == 1
        assert data["history"][0]["state"] == "pending_review"

    def test_auto_approval_criteria_serialization(self):
        criteria = AutoApprovalCriteria(
            match_score_threshold=70.0,
            completeness_threshold=80,
        )
        data = criteria.model_dump()
        assert data["match_score_threshold"] == 70.0
        assert data["completeness_threshold"] == 80


class TestEdgeCases:
    def test_review_record_default_state(self):
        record = ReviewRecord(package_id="test")
        assert record.state == ReviewState.PENDING_REVIEW
        assert record.decision is None

    def test_review_without_expiry(self):
        record = ReviewRecord(package_id="test", expires_at=None)
        assert record.expires_at is None

    def test_auto_approve_no_criteria(self):
        config = ReviewConfig(
            auto_approval_criteria=AutoApprovalCriteria(
                require_match_result=False,
                require_optimized_resume=False,
                require_cover_letter=False,
            )
        )
        validator = ReviewValidator()
        engine = DecisionEngine(validator, config)
        record = ReviewRecord(package_id="test")
        result = engine.auto_approve(record)
        assert result.state == ReviewState.AUTO_APPROVED

    def test_multiple_overrides_accumulate(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        service.create_review(pkg_id)
        service.approve(pkg_id, reviewer="user-1", reason="Good")
        service.override(
            pkg_id, reviewer="admin-1",
            new_state=ReviewState.PENDING_REVIEW,
            reason="Override 1",
        )
        service.approve(pkg_id, reviewer="user-1", reason="Re-approved")
        service.override(
            pkg_id, reviewer="admin-2",
            new_state=ReviewState.PENDING_REVIEW,
            reason="Override 2",
        )
        record = service.get_review(pkg_id)
        assert record is not None
        assert record.override_reason == "Override 2"
        assert len(record.history) == 4

    def test_reject_requires_reason(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        service.create_review(pkg_id)
        result = service.reject(
            pkg_id, reviewer="user-1", reason="Incomplete package"
        )
        assert result.reason == "Incomplete package"

    def test_approve_with_comments(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        service.create_review(pkg_id)
        result = service.approve(
            pkg_id,
            reviewer="user-1",
            reason="Good quality",
            comments="Excellent resume and cover letter",
        )
        assert result.comments == "Excellent resume and cover letter"

    def test_review_created_with_workflow_and_tracking_ids(self):
        service = ReviewService()
        pkg_id = str(uuid.uuid4())
        record = service.create_review(
            pkg_id,
            workflow_id="wf-1",
            tracking_id="tr-1",
        )
        assert record.workflow_id == "wf-1"
        assert record.tracking_id == "tr-1"
