from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from app.submission.cache import SubmissionCache
from app.submission.config import SubmissionConfig
from app.submission.dispatcher import Dispatcher
from app.submission.exceptions import (
    DuplicateSubmissionError,
    InvalidSubmissionStateError,
    SubmissionNotFoundError,
    SubmissionNotReadyError,
    SubmissionValidationError,
)
from app.submission.queue import SubmissionQueue
from app.submission.retry import RetryHandler
from app.submission.scheduler import Scheduler
from app.submission.schemas import (
    QueueItem,
    QueueStatistics,
    RetryRecord,
    StrategyType,
    SubmissionPriority,
    SubmissionRecord,
    SubmissionState,
)
from app.submission.service import SubmissionService
from app.submission.strategy import (
    ManualSubmissionStrategy,
    StrategyFactory,
    SubmissionStrategy,
)
from app.submission.validator import SubmissionValidator
from app.workflow.schemas import WorkflowState


class TestSubmissionState:
    def test_all_states_defined(self):
        expected = [
            "pending",
            "validated",
            "queued",
            "scheduled",
            "dispatched",
            "running",
            "completed",
            "failed",
            "cancelled",
        ]
        values = [s.value for s in SubmissionState]
        for exp in expected:
            assert exp in values

    def test_all_states_unique(self):
        values = [s.value for s in SubmissionState]
        assert len(values) == len(set(values))


class TestSubmissionConfig:
    def test_default_config(self):
        config = SubmissionConfig()
        assert config.cache_ttl_seconds == 300
        assert config.strict_validation is True
        assert config.dry_run_enabled is True
        assert config.default_max_retries == 3
        assert config.default_retry_delay_seconds == 60.0
        assert config.retry_backoff_multiplier == 2.0

    def test_custom_config(self):
        config = SubmissionConfig(
            cache_ttl_seconds=600,
            strict_validation=False,
            default_max_retries=5,
            default_retry_delay_seconds=30.0,
            retry_backoff_multiplier=3.0,
        )
        assert config.cache_ttl_seconds == 600
        assert config.default_max_retries == 5
        assert config.default_retry_delay_seconds == 30.0


class TestValidator:
    def test_validate_create_new(self):
        v = SubmissionValidator()
        v.validate_create("pkg-1", None)

    def test_validate_create_duplicate(self):
        v = SubmissionValidator()
        existing = SubmissionRecord(package_id="pkg-1")
        with pytest.raises(DuplicateSubmissionError):
            v.validate_create("pkg-1", existing)

    def test_validate_get_exists(self):
        v = SubmissionValidator()
        record = SubmissionRecord(package_id="test")
        result = v.validate_get(record)
        assert result.package_id == "test"

    def test_validate_get_none(self):
        v = SubmissionValidator()
        with pytest.raises(SubmissionNotFoundError):
            v.validate_get(None)

    def test_validate_submission_readiness_ready(self):
        v = SubmissionValidator()
        from app.review.schemas import ReviewState

        review = type("R", (), {"state": ReviewState.APPROVED})()
        v.validate_submission_readiness(review, WorkflowState.QUEUED, True, True, True, True)

    def test_validate_submission_readiness_not_approved(self):
        v = SubmissionValidator()
        from app.review.schemas import ReviewState

        review = type("R", (), {"state": ReviewState.PENDING_REVIEW})()
        with pytest.raises(SubmissionNotReadyError):
            v.validate_submission_readiness(review, WorkflowState.QUEUED, True, True, True, True)

    def test_validate_submission_readiness_wrong_workflow_state(self):
        v = SubmissionValidator()
        from app.review.schemas import ReviewState

        review = type("R", (), {"state": ReviewState.APPROVED})()
        with pytest.raises(SubmissionNotReadyError):
            v.validate_submission_readiness(review, WorkflowState.PACKAGE_GENERATED, True, True, True, True)

    def test_validate_submission_readiness_missing_docs(self):
        v = SubmissionValidator()
        from app.review.schemas import ReviewState

        review = type("R", (), {"state": ReviewState.APPROVED})()
        with pytest.raises(SubmissionNotReadyError):
            v.validate_submission_readiness(review, WorkflowState.QUEUED, True, False, False, False)

    def test_validate_state_transition_valid(self):
        v = SubmissionValidator()
        record = SubmissionRecord(package_id="test", state=SubmissionState.PENDING)
        v.validate_state_transition(record, SubmissionState.VALIDATED)

    def test_validate_state_transition_invalid(self):
        v = SubmissionValidator()
        record = SubmissionRecord(package_id="test", state=SubmissionState.PENDING)
        with pytest.raises(InvalidSubmissionStateError):
            v.validate_state_transition(record, SubmissionState.COMPLETED)

    def test_validate_cancel_allowed(self):
        v = SubmissionValidator()
        record = SubmissionRecord(package_id="test", state=SubmissionState.QUEUED)
        v.validate_cancel(record)

    def test_validate_cancel_not_allowed(self):
        v = SubmissionValidator()
        record = SubmissionRecord(package_id="test", state=SubmissionState.COMPLETED)
        with pytest.raises(InvalidSubmissionStateError):
            v.validate_cancel(record)

    def test_validate_retry_allowed(self):
        v = SubmissionValidator()
        record = SubmissionRecord(package_id="test", state=SubmissionState.FAILED)
        v.validate_retry(record)

    def test_validate_retry_not_failed(self):
        v = SubmissionValidator()
        record = SubmissionRecord(package_id="test", state=SubmissionState.COMPLETED)
        with pytest.raises(InvalidSubmissionStateError):
            v.validate_retry(record)

    def test_validate_retry_non_retryable(self):
        v = SubmissionValidator()
        record = SubmissionRecord(
            package_id="test",
            state=SubmissionState.FAILED,
        )
        record.retry.non_retryable = True
        with pytest.raises(SubmissionValidationError):
            v.validate_retry(record)

    def test_get_allowed_transitions_pending(self):
        allowed = SubmissionValidator._get_allowed_transitions(SubmissionState.PENDING)
        assert SubmissionState.VALIDATED in allowed
        assert SubmissionState.CANCELLED in allowed

    def test_get_allowed_transitions_failed(self):
        allowed = SubmissionValidator._get_allowed_transitions(SubmissionState.FAILED)
        assert SubmissionState.QUEUED in allowed
        assert SubmissionState.CANCELLED in allowed

    def test_get_allowed_transitions_completed(self):
        allowed = SubmissionValidator._get_allowed_transitions(SubmissionState.COMPLETED)
        assert allowed == []


class TestSubmissionQueue:
    def test_enqueue(self):
        queue = SubmissionQueue()
        record = SubmissionRecord(package_id="test")
        item = queue.enqueue(record)
        assert item.submission_id == record.id
        assert record.state == SubmissionState.QUEUED

    def test_dequeue(self):
        queue = SubmissionQueue()
        record = SubmissionRecord(package_id="test")
        queue.enqueue(record)
        item = queue.dequeue()
        assert item is not None
        assert item.submission_id == record.id

    def test_dequeue_empty(self):
        queue = SubmissionQueue()
        assert queue.dequeue() is None

    def test_dequeue_respects_priority(self):
        queue = SubmissionQueue()
        low = SubmissionRecord(package_id="low", priority=SubmissionPriority.LOW)
        high = SubmissionRecord(package_id="high", priority=SubmissionPriority.HIGH)
        queue.enqueue(low)
        queue.enqueue(high)
        first = queue.dequeue()
        assert first is not None
        assert first.submission_id == high.id

    def test_dequeue_respects_fifo_same_priority(self):
        queue = SubmissionQueue()
        r1 = SubmissionRecord(package_id="first")
        r2 = SubmissionRecord(package_id="second")
        queue.enqueue(r1)
        queue.enqueue(r2)
        first = queue.dequeue()
        assert first is not None
        assert first.submission_id == r1.id

    def test_peek(self):
        queue = SubmissionQueue()
        record = SubmissionRecord(package_id="test")
        queue.enqueue(record)
        item = queue.peek()
        assert item is not None
        assert item.submission_id == record.id
        assert queue.size == 1

    def test_peek_empty(self):
        queue = SubmissionQueue()
        assert queue.peek() is None

    def test_remove(self):
        queue = SubmissionQueue()
        record = SubmissionRecord(package_id="test")
        queue.enqueue(record)
        assert queue.remove(record.id) is True
        assert queue.size == 0

    def test_remove_nonexistent(self):
        queue = SubmissionQueue()
        assert queue.remove("nonexistent") is False

    def test_update_priority(self):
        queue = SubmissionQueue()
        record = SubmissionRecord(package_id="test", priority=SubmissionPriority.LOW)
        queue.enqueue(record)
        assert queue.update_priority(record.id, SubmissionPriority.HIGH) is True

    def test_update_priority_nonexistent(self):
        queue = SubmissionQueue()
        assert queue.update_priority("nonexistent", SubmissionPriority.HIGH) is False

    def test_get_queue(self):
        queue = SubmissionQueue()
        queue.enqueue(SubmissionRecord(package_id="a"))
        queue.enqueue(SubmissionRecord(package_id="b"))
        items = queue.get_queue()
        assert len(items) == 2

    def test_get_queue_filtered(self):
        queue = SubmissionQueue()
        rec = SubmissionRecord(package_id="a", priority=SubmissionPriority.HIGH)
        queue.enqueue(rec)
        queue.enqueue(SubmissionRecord(package_id="b", priority=SubmissionPriority.LOW))
        items = queue.get_queue(priority=SubmissionPriority.HIGH)
        assert len(items) == 1
        assert items[0].submission_id == rec.id

    def test_get_statistics(self):
        queue = SubmissionQueue()
        queue.enqueue(SubmissionRecord(package_id="a"))
        queue.enqueue(SubmissionRecord(package_id="b", priority=SubmissionPriority.HIGH))
        stats = queue.get_statistics()
        assert stats.total == 2
        assert stats.by_priority.get("medium") == 1
        assert stats.by_priority.get("high") == 1

    def test_clear(self):
        queue = SubmissionQueue()
        queue.enqueue(SubmissionRecord(package_id="a"))
        queue.enqueue(SubmissionRecord(package_id="b"))
        queue.clear()
        assert queue.is_empty

    def test_size(self):
        queue = SubmissionQueue()
        assert queue.size == 0
        queue.enqueue(SubmissionRecord(package_id="a"))
        assert queue.size == 1

    def test_thread_safety(self):
        import threading

        queue = SubmissionQueue()
        errors = []

        def worker(ident: str):
            try:
                for i in range(50):
                    r = SubmissionRecord(package_id=f"{ident}-{i}")
                    queue.enqueue(r)
                    queue.peek()
                    queue.get_statistics()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(f"t{i}",)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_dequeue_respects_scheduled_at(self):
        queue = SubmissionQueue()
        r1 = SubmissionRecord(package_id="now")
        r2 = SubmissionRecord(package_id="later")
        queue.enqueue(r1)
        queue.enqueue(r2, scheduled_at=datetime.utcnow() + timedelta(hours=1))
        first = queue.dequeue()
        assert first is not None
        assert first.submission_id == r1.id


class TestRetryHandler:
    def test_can_retry_default(self):
        handler = RetryHandler()
        record = SubmissionRecord(package_id="test")
        assert handler.can_retry(record) is True

    def test_can_retry_exhausted(self):
        handler = RetryHandler()
        record = SubmissionRecord(package_id="test")
        record.retry.max_retries = 2
        record.retry.attempt = 2
        assert handler.can_retry(record) is False

    def test_can_retry_non_retryable(self):
        handler = RetryHandler()
        record = SubmissionRecord(package_id="test")
        record.retry.non_retryable = True
        assert handler.can_retry(record) is False

    def test_get_retry_delay_exponential(self):
        handler = RetryHandler()
        record = SubmissionRecord(package_id="test")
        record.retry.retry_delay_seconds = 60.0
        record.retry.backoff_multiplier = 2.0

        record.retry.attempt = 0
        assert handler.get_retry_delay(record) == 60.0

        record.retry.attempt = 1
        assert handler.get_retry_delay(record) == 120.0

        record.retry.attempt = 2
        assert handler.get_retry_delay(record) == 240.0

    def test_record_attempt_first_failure(self):
        handler = RetryHandler()
        record = SubmissionRecord(package_id="test")
        record.retry.max_retries = 3
        result = handler.record_attempt(record, error="Timeout")
        assert result.retry.attempt == 1
        assert result.state == SubmissionState.QUEUED
        assert result.retry.next_retry_at is not None

    def test_record_attempt_exhausts_retries(self):
        handler = RetryHandler()
        record = SubmissionRecord(package_id="test")
        record.retry.max_retries = 2
        handler.record_attempt(record, error="E1")
        handler.record_attempt(record, error="E2")
        result = handler.record_attempt(record, error="E3")
        assert result.retry.attempt == 3
        assert result.state == SubmissionState.FAILED
        assert result.failed_at is not None

    def test_record_attempt_non_retryable(self):
        handler = RetryHandler()
        record = SubmissionRecord(package_id="test")
        result = handler.mark_non_retryable(record, "Invalid input")
        assert result.retry.non_retryable is True
        assert result.state == SubmissionState.FAILED

    def test_reset(self):
        handler = RetryHandler()
        record = SubmissionRecord(package_id="test")
        record.retry.attempt = 3
        record.retry.errors = ["E1", "E2"]
        record.retry.non_retryable = True
        result = handler.reset(record)
        assert result.retry.attempt == 0
        assert result.retry.errors == []
        assert result.retry.non_retryable is False


class TestScheduler:
    def test_schedule_immediate(self):
        scheduler = Scheduler()
        record = SubmissionRecord(package_id="test")
        result = scheduler.schedule(record, delay_seconds=0)
        assert result.state == SubmissionState.SCHEDULED
        assert result.scheduled_at is not None

    def test_schedule_with_delay(self):
        scheduler = Scheduler()
        record = SubmissionRecord(package_id="test")
        result = scheduler.schedule(record, delay_seconds=3600)
        assert result.state == SubmissionState.SCHEDULED
        assert result.scheduled_at > datetime.utcnow()

    def test_is_due_no_schedule(self):
        scheduler = Scheduler()
        record = SubmissionRecord(package_id="test")
        assert scheduler.is_due(record) is True

    def test_is_due_future(self):
        scheduler = Scheduler()
        record = SubmissionRecord(package_id="test")
        record.scheduled_at = datetime.utcnow() + timedelta(hours=1)
        assert scheduler.is_due(record) is False

    def test_is_due_past(self):
        scheduler = Scheduler()
        record = SubmissionRecord(package_id="test")
        record.scheduled_at = datetime.utcnow() - timedelta(hours=1)
        assert scheduler.is_due(record) is True

    def test_reschedule(self):
        scheduler = Scheduler()
        record = SubmissionRecord(package_id="test")
        result = scheduler.reschedule(record, 7200)
        assert result.state == SubmissionState.SCHEDULED
        assert result.scheduled_at > datetime.utcnow()

    def test_cancel_schedule(self):
        scheduler = Scheduler()
        record = SubmissionRecord(package_id="test")
        record.scheduled_at = datetime.utcnow() + timedelta(hours=1)
        result = scheduler.cancel_schedule(record)
        assert result.scheduled_at is None


class TestStrategy:
    def test_manual_strategy_type(self):
        strategy = ManualSubmissionStrategy()
        assert strategy.get_strategy_type() == StrategyType.MANUAL

    def test_manual_strategy_execute(self):
        strategy = ManualSubmissionStrategy()
        record = SubmissionRecord(package_id="test")
        result = strategy.execute(record)
        assert result.state == SubmissionState.COMPLETED
        assert result.completed_at is not None

    def test_manual_strategy_validate_environment(self):
        strategy = ManualSubmissionStrategy()
        assert strategy.validate_environment() == []

    def test_manual_strategy_required_fields(self):
        strategy = ManualSubmissionStrategy()
        assert strategy.get_required_fields() == ["package_id"]

    def test_strategy_factory_create_manual(self):
        strategy = StrategyFactory.create(StrategyType.MANUAL)
        assert isinstance(strategy, ManualSubmissionStrategy)

    def test_strategy_factory_unknown(self):
        with pytest.raises(ValueError):
            StrategyFactory.create("unknown")

    def test_strategy_factory_register(self):
        class TestStrategy(SubmissionStrategy):
            def get_strategy_type(self):
                return StrategyType.MANUAL

            def execute(self, r):
                return r

            def validate_environment(self):
                return []

            def get_required_fields(self):
                return []

        StrategyFactory.register(StrategyType.PLAYWRIGHT, TestStrategy)
        strategy = StrategyFactory.create(StrategyType.PLAYWRIGHT)
        assert isinstance(strategy, TestStrategy)


class TestDispatcher:
    def test_dispatch_dry_run(self):
        handler = RetryHandler()
        dispatcher = Dispatcher(handler)
        record = SubmissionRecord(package_id="test", dry_run=True)
        result = dispatcher.dispatch(record)
        assert result.state == SubmissionState.DISPATCHED
        assert result.metadata.get("dry_run") is True

    def test_dispatch_manual_strategy(self):
        handler = RetryHandler()
        dispatcher = Dispatcher(handler)
        record = SubmissionRecord(package_id="test")
        result = dispatcher.dispatch(record, StrategyType.MANUAL)
        assert result.state == SubmissionState.COMPLETED

    def test_dispatch_handles_exception(self):
        handler = RetryHandler()
        dispatcher = Dispatcher(handler)
        record = SubmissionRecord(package_id="test")
        record.retry.max_retries = 0

        with patch.object(
            StrategyFactory,
            "create",
            side_effect=Exception("Strategy error"),
        ):
            result = dispatcher.dispatch(record, StrategyType.MANUAL)
            assert result.state == SubmissionState.FAILED
            assert len(result.retry.errors) > 0

    def test_get_available_strategies(self):
        handler = RetryHandler()
        dispatcher = Dispatcher(handler)
        strategies = dispatcher.get_available_strategies()
        assert StrategyType.MANUAL in strategies


class TestSubmissionCache:
    def test_set_and_get(self):
        config = SubmissionConfig(cache_ttl_seconds=300)
        cache = SubmissionCache(config)
        record = SubmissionRecord(package_id="test")
        cache.set("k1", record)
        result = cache.get("k1")
        assert result is not None
        assert result.package_id == "test"

    def test_get_missing(self):
        config = SubmissionConfig()
        cache = SubmissionCache(config)
        assert cache.get("nonexistent") is None

    def test_invalidate(self):
        config = SubmissionConfig()
        cache = SubmissionCache(config)
        cache.set("k1", SubmissionRecord(package_id="test"))
        cache.invalidate("k1")
        assert cache.get("k1") is None

    def test_clear(self):
        config = SubmissionConfig()
        cache = SubmissionCache(config)
        cache.set("k1", SubmissionRecord(package_id="t1"))
        cache.set("k2", SubmissionRecord(package_id="t2"))
        cache.clear()
        assert cache.get("k1") is None
        assert cache.get("k2") is None

    def test_thread_safety(self):
        import threading

        config = SubmissionConfig()
        cache = SubmissionCache(config)
        errors = []

        def worker(ident: str):
            try:
                for i in range(100):
                    key = f"{ident}-{i}"
                    cache.set(key, SubmissionRecord(package_id=key))
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


class TestSubmissionService:
    def test_create_submission(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        record = service.create_submission(pkg_id)
        assert record.package_id == pkg_id
        assert record.state == SubmissionState.PENDING

    def test_create_submission_with_all_fields(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        record = service.create_submission(
            pkg_id,
            workflow_id="wf-1",
            tracking_id="tr-1",
            review_id="rev-1",
            priority=SubmissionPriority.HIGH,
            strategy=StrategyType.MANUAL,
            dry_run=True,
            metadata={"source": "auto"},
        )
        assert record.workflow_id == "wf-1"
        assert record.tracking_id == "tr-1"
        assert record.priority == SubmissionPriority.HIGH
        assert record.dry_run is True

    def test_create_duplicate_submission(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        service.create_submission(pkg_id)
        with pytest.raises(DuplicateSubmissionError):
            service.create_submission(pkg_id)

    def test_validate_ready(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        service.create_submission(pkg_id)
        result = service.validate(
            pkg_id,
            review_status="approved",
            workflow_status="queued",
            is_package_complete=True,
            has_job_posting=True,
            has_resume=True,
            has_cover_letter=True,
        )
        assert result.state == SubmissionState.VALIDATED

    def test_validate_not_ready(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        service.create_submission(pkg_id)
        with pytest.raises(SubmissionNotReadyError):
            service.validate(
                pkg_id,
                review_status="pending_review",
                workflow_status="queued",
                is_package_complete=True,
                has_job_posting=True,
                has_resume=True,
                has_cover_letter=True,
            )

    def test_queue(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        record = service.create_submission(pkg_id)
        record.state = SubmissionState.VALIDATED
        service._cache.set(pkg_id, record)
        result = service.queue(pkg_id)
        assert result.state == SubmissionState.QUEUED

    def test_dispatch(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        record = service.create_submission(pkg_id)
        record.state = SubmissionState.QUEUED
        service._cache.set(pkg_id, record)
        result = service.dispatch(pkg_id)
        assert result.state in (SubmissionState.COMPLETED, SubmissionState.DISPATCHED)

    def test_cancel(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        record = service.create_submission(pkg_id)
        record.state = SubmissionState.QUEUED
        service._cache.set(pkg_id, record)
        service._queue.enqueue(record)
        result = service.cancel(pkg_id, reason="User cancelled")
        assert result.state == SubmissionState.CANCELLED

    def test_cancel_invalid_state(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        record = service.create_submission(pkg_id)
        record.state = SubmissionState.COMPLETED
        service._cache.set(pkg_id, record)
        with pytest.raises(InvalidSubmissionStateError):
            service.cancel(pkg_id)

    def test_retry(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        record = service.create_submission(pkg_id)
        record.state = SubmissionState.FAILED
        record.retry.attempt = 2
        service._cache.set(pkg_id, record)
        result = service.retry(pkg_id)
        assert result.state == SubmissionState.QUEUED
        assert result.retry.attempt == 0

    def test_retry_not_failed(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        service.create_submission(pkg_id)
        with pytest.raises(InvalidSubmissionStateError):
            service.retry(pkg_id)

    def test_get_status(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        service.create_submission(pkg_id)
        status = service.get_status(pkg_id)
        assert status is not None
        assert status.package_id == pkg_id

    def test_get_status_nonexistent(self):
        service = SubmissionService()
        assert service.get_status("nonexistent") is None

    def test_get_queue(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        record = service.create_submission(pkg_id)
        record.state = SubmissionState.QUEUED
        service._cache.set(pkg_id, record)
        service._queue.enqueue(record)
        items = service.get_queue()
        assert len(items) >= 1

    def test_get_queue_statistics(self):
        service = SubmissionService()
        stats = service.get_queue_statistics()
        assert stats.total >= 0

    def test_update_priority(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        record = service.create_submission(pkg_id)
        record.state = SubmissionState.QUEUED
        service._cache.set(pkg_id, record)
        service._queue.enqueue(record)
        result = service.update_priority(pkg_id, SubmissionPriority.HIGH)
        assert result.priority == SubmissionPriority.HIGH

    def test_invalidate_cache(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        service.create_submission(pkg_id)
        service.invalidate_cache(pkg_id)
        assert service.get_status(pkg_id) is None

    def test_clear_cache(self):
        service = SubmissionService()
        p1 = str(uuid.uuid4())
        p2 = str(uuid.uuid4())
        service.create_submission(p1)
        service.create_submission(p2)
        service.clear_cache()
        assert service.get_status(p1) is None
        assert service.get_status(p2) is None

    def test_full_submission_lifecycle(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        service.create_submission(pkg_id)
        service.validate(
            pkg_id,
            review_status="approved",
            workflow_status="queued",
            is_package_complete=True,
            has_job_posting=True,
            has_resume=True,
            has_cover_letter=True,
        )
        service.queue(pkg_id)
        result = service.dispatch(pkg_id)
        assert result.state == SubmissionState.COMPLETED

    def test_deterministic_behavior(self):
        service = SubmissionService()
        p1 = str(uuid.uuid4())
        p2 = str(uuid.uuid4())
        service.create_submission(p1, priority=SubmissionPriority.HIGH)
        service.create_submission(p2, priority=SubmissionPriority.HIGH)
        s1 = service.get_status(p1)
        s2 = service.get_status(p2)
        assert s1 is not None and s2 is not None
        assert s1.state == s2.state
        assert s1.priority == s2.priority

    def test_nonexistent_operations_raise(self):
        service = SubmissionService()
        with pytest.raises(SubmissionNotFoundError):
            service.validate("nonexistent")
        with pytest.raises(SubmissionNotFoundError):
            service.queue("nonexistent")
        with pytest.raises(SubmissionNotFoundError):
            service.dispatch("nonexistent")
        with pytest.raises(SubmissionNotFoundError):
            service.cancel("nonexistent")
        with pytest.raises(SubmissionNotFoundError):
            service.retry("nonexistent")


class TestSerialization:
    def test_submission_record_serialization(self):
        record = SubmissionRecord(
            package_id="pkg-1",
            state=SubmissionState.QUEUED,
        )
        data = record.model_dump()
        assert data["package_id"] == "pkg-1"
        assert data["state"] == "queued"

    def test_submission_record_with_retry(self):
        record = SubmissionRecord(
            package_id="test",
            retry=RetryRecord(attempt=2, max_retries=5),
        )
        data = record.model_dump()
        assert data["retry"]["attempt"] == 2
        assert data["retry"]["max_retries"] == 5

    def test_queue_item_serialization(self):
        item = QueueItem(
            submission_id="s-1",
            priority=SubmissionPriority.HIGH,
        )
        data = item.model_dump()
        assert data["submission_id"] == "s-1"
        assert data["priority"] == 2

    def test_queue_statistics_serialization(self):
        stats = QueueStatistics(
            total=5,
            by_priority={"high": 2, "medium": 3},
        )
        data = stats.model_dump()
        assert data["total"] == 5
        assert data["by_priority"]["high"] == 2


class TestEdgeCases:
    def test_submission_default_state(self):
        record = SubmissionRecord(package_id="test")
        assert record.state == SubmissionState.PENDING

    def test_submission_default_priority(self):
        record = SubmissionRecord(package_id="test")
        assert record.priority == SubmissionPriority.MEDIUM

    def test_dry_run_does_not_execute_strategy(self):
        service = SubmissionService()
        pkg_id = str(uuid.uuid4())
        record = service.create_submission(pkg_id, dry_run=True)
        record.state = SubmissionState.QUEUED
        service._cache.set(pkg_id, record)
        result = service.dispatch(pkg_id)
        assert result.state == SubmissionState.DISPATCHED
        assert result.metadata.get("dry_run") is True

    def test_dispatcher_with_exception_becomes_failed(self):
        handler = RetryHandler()
        dispatcher = Dispatcher(handler)
        record = SubmissionRecord(package_id="test", retry=RetryRecord(max_retries=0))
        record.state = SubmissionState.DISPATCHED

        with patch.object(
            ManualSubmissionStrategy,
            "execute",
            side_effect=Exception("Execution error"),
        ):
            result = dispatcher.dispatch(record, StrategyType.MANUAL)
            assert result.state == SubmissionState.FAILED

    def test_multiple_failures_exhaust_retries(self):
        handler = RetryHandler()
        record = SubmissionRecord(package_id="test", retry=RetryRecord(max_retries=2))
        handler.record_attempt(record, "E1")
        handler.record_attempt(record, "E2")
        result = handler.record_attempt(record, "E3")
        assert result.state == SubmissionState.FAILED
        assert result.retry.attempt == 3

    def test_cancelled_submission_prevents_further_actions(self):
        v = SubmissionValidator()
        record = SubmissionRecord(package_id="test", state=SubmissionState.CANCELLED)
        with pytest.raises(InvalidSubmissionStateError):
            v.validate_state_transition(record, SubmissionState.QUEUED)

    def test_completed_submission_prevents_further_actions(self):
        v = SubmissionValidator()
        record = SubmissionRecord(package_id="test", state=SubmissionState.COMPLETED)
        with pytest.raises(InvalidSubmissionStateError):
            v.validate_state_transition(record, SubmissionState.QUEUED)

    def test_scheduler_no_op_for_zero_delay(self):
        scheduler = Scheduler()
        record = SubmissionRecord(package_id="test")
        result = scheduler.schedule(record, delay_seconds=0)
        assert result.state == SubmissionState.SCHEDULED

    def test_queue_with_scheduled_future_not_dequeuable(self):
        queue = SubmissionQueue()
        record = SubmissionRecord(package_id="test")
        queue.enqueue(record, scheduled_at=datetime.utcnow() + timedelta(hours=2))
        assert queue.dequeue() is None
