from __future__ import annotations

import time
import uuid
from datetime import datetime, timedelta
from threading import Thread

import pytest

from app.automation.cache import AutomationCache
from app.automation.config import AutomationConfig
from app.automation.exceptions import (
    DuplicateJobError,
    InvalidCronExpressionError,
    InvalidScheduleError,
    InvalidTriggerError,
    JobDisabledError,
    JobNotFoundError,
    JobPausedError,
    MissingTargetError,
    QueueFullError,
    RetryLimitExceededError,
)
from app.automation.history import ExecutionHistory
from app.automation.jobs import JobManager
from app.automation.policies import PolicyEnforcer
from app.automation.queue import AutomationQueue
from app.automation.scheduler import AutomationScheduler
from app.automation.schemas import (
    AutomationJob,
    AutomationPolicy,
    AutomationTrigger,
    AutomationType,
    ExecutionRecord,
    ExecutionStatus,
    HistoryQuery,
    JobPriority,
    JobState,
    TriggerType,
)
from app.automation.service import AutomationService
from app.automation.triggers import TriggerEvaluator
from app.automation.validator import AutomationValidator


def _make_job(
    job_id: str | None = None,
    name: str = "test-job",
    target_module: str = "jobs",
    target_action: str = "search",
    **overrides: dict,
) -> AutomationJob:
    kwargs: dict = {
        "id": job_id or str(uuid.uuid4()),
        "name": name,
        "target_module": target_module,
        "target_action": target_action,
    }
    kwargs.update(overrides)
    return AutomationJob(**kwargs)


class TestAutomationType:
    def test_all_types_defined(self):
        expected = ["manual", "one_time", "recurring", "event_driven"]
        values = [t.value for t in AutomationType]
        for exp in expected:
            assert exp in values

    def test_enum_values(self):
        assert AutomationType.MANUAL.value == "manual"
        assert AutomationType.ONE_TIME.value == "one_time"
        assert AutomationType.RECURRING.value == "recurring"
        assert AutomationType.EVENT_DRIVEN.value == "event_driven"


class TestTriggerType:
    def test_all_triggers_defined(self):
        expected = [
            "immediate", "scheduled", "daily", "weekly", "monthly",
            "cron", "workflow_event", "review_approval",
            "submission_completion", "manual",
        ]
        values = [t.value for t in TriggerType]
        for exp in expected:
            assert exp in values


class TestJobPriority:
    def test_priority_values(self):
        assert JobPriority.LOW.value == 0
        assert JobPriority.MEDIUM.value == 1
        assert JobPriority.HIGH.value == 2
        assert JobPriority.CRITICAL.value == 3


class TestJobState:
    def test_state_values(self):
        assert JobState.ACTIVE.value == "active"
        assert JobState.PAUSED.value == "paused"
        assert JobState.COMPLETED.value == "completed"
        assert JobState.FAILED.value == "failed"
        assert JobState.CANCELLED.value == "cancelled"


class TestExecutionStatus:
    def test_all_statuses_defined(self):
        expected = [
            "pending", "running", "completed", "failed",
            "cancelled", "retried", "skipped",
        ]
        values = [s.value for s in ExecutionStatus]
        for exp in expected:
            assert exp in values


class TestAutomationConfig:
    def test_defaults(self):
        config = AutomationConfig()
        assert config.cache_ttl_seconds == 300
        assert config.strict_validation is True
        assert config.default_max_retries == 3
        assert config.max_concurrent_jobs == 5
        assert config.execution_timeout_seconds == 3600.0

    def test_custom_values(self):
        config = AutomationConfig(
            cache_ttl_seconds=600,
            strict_validation=False,
            default_max_retries=5,
        )
        assert config.cache_ttl_seconds == 600
        assert config.strict_validation is False
        assert config.default_max_retries == 5


class TestAutomationTrigger:
    def test_default_trigger(self):
        trigger = AutomationTrigger()
        assert trigger.trigger_type == TriggerType.MANUAL
        assert trigger.scheduled_at is None
        assert trigger.cron_expression is None

    def test_scheduled_trigger(self):
        dt = datetime.utcnow() + timedelta(hours=1)
        trigger = AutomationTrigger(
            trigger_type=TriggerType.SCHEDULED,
            scheduled_at=dt,
        )
        assert trigger.trigger_type == TriggerType.SCHEDULED
        assert trigger.scheduled_at == dt

    def test_cron_trigger(self):
        trigger = AutomationTrigger(
            trigger_type=TriggerType.CRON,
            cron_expression="0 9 * * 1",
        )
        assert trigger.cron_expression == "0 9 * * 1"

    def test_daily_trigger(self):
        trigger = AutomationTrigger(
            trigger_type=TriggerType.DAILY,
            daily_time="09:00",
        )
        assert trigger.daily_time == "09:00"

    def test_weekly_trigger(self):
        trigger = AutomationTrigger(
            trigger_type=TriggerType.WEEKLY,
            weekly_day=0,
            weekly_time="10:00",
        )
        assert trigger.weekly_day == 0
        assert trigger.weekly_time == "10:00"

    def test_monthly_trigger(self):
        trigger = AutomationTrigger(
            trigger_type=TriggerType.MONTHLY,
            monthly_day=1,
            monthly_time="12:00",
        )
        assert trigger.monthly_day == 1
        assert trigger.monthly_time == "12:00"


class TestAutomationPolicy:
    def test_default_policy(self):
        policy = AutomationPolicy()
        assert policy.auto_search_jobs is False
        assert policy.require_review is True
        assert policy.max_retries == 3

    def test_custom_policy(self):
        policy = AutomationPolicy(
            auto_search_jobs=True,
            auto_approve_threshold=0.8,
            max_retries=5,
        )
        assert policy.auto_search_jobs is True
        assert policy.auto_approve_threshold == 0.8
        assert policy.max_retries == 5


class TestAutomationJob:
    def test_default_job(self):
        job = _make_job()
        assert job.enabled is True
        assert job.priority == JobPriority.MEDIUM
        assert job.state == JobState.ACTIVE
        assert job.target_module == "jobs"
        assert job.target_action == "search"

    def test_custom_job(self):
        job_id = "custom-id"
        job = _make_job(
            job_id=job_id,
            name="Custom Job",
            priority=JobPriority.HIGH,
            state=JobState.PAUSED,
        )
        assert job.id == job_id
        assert job.name == "Custom Job"
        assert job.priority == JobPriority.HIGH
        assert job.state == JobState.PAUSED

    def test_serialization(self):
        job = _make_job()
        data = job.model_dump()
        restored = AutomationJob(**data)
        assert restored.id == job.id
        assert restored.name == job.name
        assert restored.target_module == job.target_module
        assert restored.target_action == job.target_action
        assert restored.priority == job.priority
        assert restored.state == job.state

    def test_trigger_nested_serialization(self):
        trigger = AutomationTrigger(
            trigger_type=TriggerType.DAILY,
            daily_time="08:00",
        )
        job = _make_job(trigger=trigger)
        data = job.model_dump()
        restored = AutomationJob(**data)
        assert restored.trigger.trigger_type == TriggerType.DAILY
        assert restored.trigger.daily_time == "08:00"

    def test_policy_nested_serialization(self):
        policy = AutomationPolicy(auto_search_jobs=True, max_retries=5)
        job = _make_job(policy=policy)
        data = job.model_dump()
        restored = AutomationJob(**data)
        assert restored.policy.auto_search_jobs is True
        assert restored.policy.max_retries == 5


class TestTriggerEvaluator:
    def test_validate_valid_cron(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.CRON,
            cron_expression="0 9 * * 1",
        )
        errors = evaluator.validate(trigger)
        assert len(errors) == 0

    def test_validate_invalid_cron(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.CRON,
            cron_expression="invalid",
        )
        errors = evaluator.validate(trigger)
        assert len(errors) > 0

    def test_validate_missing_cron_expr(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(trigger_type=TriggerType.CRON)
        errors = evaluator.validate(trigger)
        assert len(errors) > 0
        assert any("Cron expression" in e for e in errors)

    def test_validate_missing_scheduled_at(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(trigger_type=TriggerType.SCHEDULED)
        errors = evaluator.validate(trigger)
        assert any("scheduled_at" in e for e in errors)

    def test_validate_missing_daily_time(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(trigger_type=TriggerType.DAILY)
        errors = evaluator.validate(trigger)
        assert any("daily_time" in e for e in errors)

    def test_validate_missing_weekly_fields(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(trigger_type=TriggerType.WEEKLY)
        errors = evaluator.validate(trigger)
        assert any("weekly_day" in e for e in errors)
        assert any("weekly_time" in e for e in errors)

    def test_validate_missing_monthly_fields(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(trigger_type=TriggerType.MONTHLY)
        errors = evaluator.validate(trigger)
        assert any("monthly_day" in e for e in errors)
        assert any("monthly_time" in e for e in errors)

    def test_validate_missing_event_source(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(trigger_type=TriggerType.WORKFLOW_EVENT)
        errors = evaluator.validate(trigger)
        assert any("event_source" in e for e in errors)

    def test_validate_valid_event_source(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.WORKFLOW_EVENT,
            event_source="workflow.completed",
        )
        errors = evaluator.validate(trigger)
        assert len(errors) == 0

    def test_evaluate_immediate_true(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(trigger_type=TriggerType.IMMEDIATE)
        assert evaluator.evaluate(trigger) is True

    def test_evaluate_scheduled_due(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.SCHEDULED,
            scheduled_at=datetime.utcnow() - timedelta(seconds=1),
        )
        assert evaluator.evaluate(trigger) is True

    def test_evaluate_scheduled_not_due(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.SCHEDULED,
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
        )
        assert evaluator.evaluate(trigger) is False

    def test_evaluate_manual_false(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(trigger_type=TriggerType.MANUAL)
        assert evaluator.evaluate(trigger) is False

    def test_evaluate_event_false(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.WORKFLOW_EVENT,
            event_source="workflow.completed",
        )
        assert evaluator.evaluate(trigger) is False

    def test_calculate_next_run_immediate(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(trigger_type=TriggerType.IMMEDIATE)
        result = evaluator.calculate_next_run(trigger)
        assert result is not None
        assert (datetime.utcnow() - result).total_seconds() < 1

    def test_calculate_next_run_scheduled(self):
        evaluator = TriggerEvaluator()
        dt = datetime.utcnow() + timedelta(hours=2)
        trigger = AutomationTrigger(
            trigger_type=TriggerType.SCHEDULED,
            scheduled_at=dt,
        )
        result = evaluator.calculate_next_run(trigger)
        assert result == dt

    def test_calculate_next_run_daily(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.DAILY,
            daily_time="12:00",
        )
        result = evaluator.calculate_next_run(trigger)
        assert result is not None
        assert result.hour == 12
        assert result.minute == 0

    def test_calculate_next_run_weekly(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.WEEKLY,
            weekly_day=datetime.utcnow().weekday(),
            weekly_time="14:00",
        )
        result = evaluator.calculate_next_run(trigger)
        assert result is not None
        assert result.hour == 14
        assert result.minute == 0

    def test_calculate_next_run_manual_none(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(trigger_type=TriggerType.MANUAL)
        result = evaluator.calculate_next_run(trigger)
        assert result is None

    def test_calculate_next_run_event_none(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.REVIEW_APPROVAL,
            event_source="review.approved",
        )
        result = evaluator.calculate_next_run(trigger)
        assert result is None

    def test_calculate_next_run_cron_none(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.CRON,
            cron_expression="0 9 * * 1",
        )
        result = evaluator.calculate_next_run(trigger)
        assert result is None

    def test_calculate_next_run_daily_future(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.DAILY,
            daily_time="23:59",
        )
        result = evaluator.calculate_next_run(trigger)
        assert result is not None

    def test_calculate_next_run_monthly(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.MONTHLY,
            monthly_day=15,
            monthly_time="10:00",
        )
        result = evaluator.calculate_next_run(trigger)
        if result is not None:
            assert result.day == 15

    def test_parse_time_today(self):
        result = TriggerEvaluator._parse_time_today("08:30:00")
        assert result is not None
        assert result.hour == 8
        assert result.minute == 30
        assert result.second == 0

    def test_parse_time_today_invalid(self):
        result = TriggerEvaluator._parse_time_today("invalid")
        assert result is None


class TestAutomationValidator:
    def test_validate_create_new(self):
        validator = AutomationValidator()
        job = _make_job()
        validator.validate_create(job, None)

    def test_validate_create_duplicate(self):
        validator = AutomationValidator()
        job = _make_job()
        with pytest.raises(DuplicateJobError):
            validator.validate_create(job, job)

    def test_validate_update_existing(self):
        validator = AutomationValidator()
        job = _make_job()
        result = validator.validate_update(job, job)
        assert result == job

    def test_validate_update_not_found(self):
        validator = AutomationValidator()
        job = _make_job()
        with pytest.raises(JobNotFoundError):
            validator.validate_update(job, None)

    def test_validate_get_found(self):
        validator = AutomationValidator()
        job = _make_job()
        result = validator.validate_get(job)
        assert result == job

    def test_validate_get_not_found(self):
        validator = AutomationValidator()
        with pytest.raises(JobNotFoundError):
            validator.validate_get(None)

    def test_validate_execution_enabled_active(self):
        validator = AutomationValidator()
        job = _make_job(enabled=True)
        job.state = JobState.ACTIVE
        validator.validate_execution(job)

    def test_validate_execution_disabled(self):
        validator = AutomationValidator()
        job = _make_job(enabled=False)
        with pytest.raises(JobDisabledError):
            validator.validate_execution(job)

    def test_validate_execution_paused(self):
        validator = AutomationValidator()
        job = _make_job(enabled=True)
        job.state = JobState.PAUSED
        with pytest.raises(JobPausedError):
            validator.validate_execution(job)

    def test_validate_execution_completed(self):
        validator = AutomationValidator()
        job = _make_job(enabled=True)
        job.state = JobState.COMPLETED
        with pytest.raises(JobDisabledError):
            validator.validate_execution(job)

    def test_validate_execution_missing_target(self):
        validator = AutomationValidator()
        job = _make_job(target_module="", target_action="")
        with pytest.raises(MissingTargetError):
            validator.validate_execution(job)

    def test_validate_retry_within_limits(self):
        validator = AutomationValidator()
        job = _make_job()
        job.retry_count = 2
        job.policy.max_retries = 3
        validator.validate_retry(job)

    def test_validate_retry_exhausted(self):
        validator = AutomationValidator()
        job = _make_job()
        job.retry_count = 3
        job.policy.max_retries = 3
        with pytest.raises(RetryLimitExceededError):
            validator.validate_retry(job)

    def test_validate_cancel_active(self):
        validator = AutomationValidator()
        job = _make_job()
        validator.validate_cancel(job)

    def test_validate_cancel_already_cancelled(self):
        validator = AutomationValidator()
        job = _make_job()
        job.state = JobState.CANCELLED
        with pytest.raises(JobDisabledError):
            validator.validate_cancel(job)

    def test_validate_trigger_valid(self):
        validator = AutomationValidator()
        trigger = AutomationTrigger(trigger_type=TriggerType.DAILY, daily_time="09:00")
        validator.validate_trigger(trigger)

    def test_validate_trigger_invalid_cron(self):
        validator = AutomationValidator()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.CRON,
            cron_expression="bad",
        )
        with pytest.raises(InvalidCronExpressionError):
            validator.validate_trigger(trigger)

    def test_validate_trigger_invalid(self):
        validator = AutomationValidator()
        trigger = AutomationTrigger(trigger_type=TriggerType.DAILY)
        with pytest.raises(InvalidTriggerError):
            validator.validate_trigger(trigger)

    def test_validate_schedule_one_time_manual(self):
        validator = AutomationValidator()
        job = _make_job(
            automation_type=AutomationType.ONE_TIME,
            trigger=AutomationTrigger(trigger_type=TriggerType.MANUAL),
        )
        with pytest.raises(InvalidScheduleError):
            validator.validate_schedule(job)

    def test_validate_schedule_one_time_non_manual(self):
        validator = AutomationValidator()
        job = _make_job(
            automation_type=AutomationType.ONE_TIME,
            trigger=AutomationTrigger(
                trigger_type=TriggerType.SCHEDULED,
                scheduled_at=datetime.utcnow() + timedelta(hours=1),
            ),
        )
        validator.validate_schedule(job)

    def test_validate_missing_target_module(self):
        validator = AutomationValidator(strict=False)
        job = _make_job(target_module="")
        with pytest.raises(MissingTargetError):
            validator.validate_create(job, None)

    def test_validate_missing_target_action(self):
        validator = AutomationValidator(strict=False)
        job = _make_job(target_action="")
        with pytest.raises(MissingTargetError):
            validator.validate_create(job, None)


class TestAutomationCache:
    def test_set_and_get(self):
        config = AutomationConfig(cache_ttl_seconds=300)
        cache = AutomationCache(config)
        job = _make_job()
        cache.set("test-key", job)
        result = cache.get("test-key")
        assert result is not None
        assert result.id == job.id

    def test_get_nonexistent(self):
        config = AutomationConfig(cache_ttl_seconds=300)
        cache = AutomationCache(config)
        result = cache.get("nonexistent")
        assert result is None

    def test_invalidate(self):
        config = AutomationConfig(cache_ttl_seconds=300)
        cache = AutomationCache(config)
        cache.set("key", "value")
        cache.invalidate("key")
        assert cache.get("key") is None

    def test_clear(self):
        config = AutomationConfig(cache_ttl_seconds=300)
        cache = AutomationCache(config)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_ttl_expiry(self):
        config = AutomationConfig(cache_ttl_seconds=0)
        cache = AutomationCache(config)
        cache.set("key", "value")
        time.sleep(0.01)
        result = cache.get("key")
        assert result is None

    def test_thread_safety(self):
        config = AutomationConfig(cache_ttl_seconds=300)
        cache = AutomationCache(config)
        errors: list[Exception] = []

        def worker(n: int) -> None:
            try:
                for i in range(100):
                    cache.set(f"key-{n}-{i}", i)
                    cache.get(f"key-{n}-{i}")
            except Exception as e:
                errors.append(e)

        threads = [Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0


class TestJobManager:
    def test_add_and_get(self):
        mgr = JobManager()
        job = _make_job()
        mgr.add(job)
        assert mgr.get(job.id) == job

    def test_get_nonexistent(self):
        mgr = JobManager()
        assert mgr.get("nonexistent") is None

    def test_update(self):
        mgr = JobManager()
        job = _make_job(name="original")
        mgr.add(job)
        job.name = "updated"
        mgr.update(job)
        assert mgr.get(job.id).name == "updated"

    def test_remove(self):
        mgr = JobManager()
        job = _make_job()
        mgr.add(job)
        assert mgr.remove(job.id) is True
        assert mgr.get(job.id) is None

    def test_remove_nonexistent(self):
        mgr = JobManager()
        assert mgr.remove("nonexistent") is False

    def test_list_jobs(self):
        mgr = JobManager()
        j1 = _make_job(job_id="a", priority=JobPriority.HIGH)
        j2 = _make_job(job_id="b", priority=JobPriority.LOW)
        mgr.add(j1)
        mgr.add(j2)
        jobs = mgr.list_jobs()
        assert len(jobs) == 2
        assert jobs[0].priority == JobPriority.HIGH

    def test_list_jobs_filter_by_state(self):
        mgr = JobManager()
        j1 = _make_job(job_id="a", state=JobState.ACTIVE)
        j2 = _make_job(job_id="b", state=JobState.PAUSED)
        mgr.add(j1)
        mgr.add(j2)
        active = mgr.list_jobs(state=JobState.ACTIVE)
        assert len(active) == 1
        assert active[0].id == "a"

    def test_list_jobs_filter_by_priority(self):
        mgr = JobManager()
        j1 = _make_job(job_id="a", priority=JobPriority.HIGH)
        j2 = _make_job(job_id="b", priority=JobPriority.LOW)
        mgr.add(j1)
        mgr.add(j2)
        high = mgr.list_jobs(priority=JobPriority.HIGH)
        assert len(high) == 1
        assert high[0].id == "a"

    def test_get_enabled_jobs(self):
        mgr = JobManager()
        j1 = _make_job(job_id="a", enabled=True, state=JobState.ACTIVE)
        j2 = _make_job(job_id="b", enabled=False, state=JobState.ACTIVE)
        j3 = _make_job(job_id="c", enabled=True, state=JobState.PAUSED)
        mgr.add(j1)
        mgr.add(j2)
        mgr.add(j3)
        enabled = mgr.get_enabled_jobs()
        assert len(enabled) == 1
        assert enabled[0].id == "a"

    def test_count(self):
        mgr = JobManager()
        assert mgr.count() == 0
        mgr.add(_make_job())
        assert mgr.count() == 1


class TestAutomationQueue:
    def test_enqueue_and_dequeue(self):
        queue = AutomationQueue()
        job = _make_job()
        item = queue.enqueue(job)
        assert item.job_id == job.id
        assert item.priority == job.priority
        dequeued = queue.dequeue()
        assert dequeued is not None
        assert dequeued.job_id == job.id

    def test_dequeue_empty(self):
        queue = AutomationQueue()
        assert queue.dequeue() is None

    def test_peek(self):
        queue = AutomationQueue()
        job = _make_job()
        queue.enqueue(job)
        peeked = queue.peek()
        assert peeked is not None
        assert peeked.job_id == job.id
        assert queue.size == 1

    def test_remove(self):
        queue = AutomationQueue()
        job = _make_job()
        queue.enqueue(job)
        assert queue.remove(job.id) is True
        assert queue.size == 0

    def test_remove_nonexistent(self):
        queue = AutomationQueue()
        assert queue.remove("nonexistent") is False

    def test_priority_ordering(self):
        queue = AutomationQueue()
        low_job = _make_job(job_id="low", priority=JobPriority.LOW)
        high_job = _make_job(job_id="high", priority=JobPriority.HIGH)
        queue.enqueue(low_job)
        queue.enqueue(high_job)
        first = queue.dequeue()
        assert first is not None
        assert first.job_id == "high"

    def test_pause_and_resume(self):
        queue = AutomationQueue()
        assert queue.is_paused() is False
        queue.pause()
        assert queue.is_paused() is True
        job = _make_job()
        queue.enqueue(job)
        assert queue.dequeue() is None
        queue.resume()
        assert queue.is_paused() is False
        assert queue.dequeue() is not None

    def test_update_priority(self):
        queue = AutomationQueue()
        job = _make_job(job_id="test", priority=JobPriority.LOW)
        queue.enqueue(job)
        assert queue.update_priority("test", JobPriority.HIGH) is True
        assert queue.peek().priority == JobPriority.HIGH

    def test_update_priority_nonexistent(self):
        queue = AutomationQueue()
        assert queue.update_priority("nonexistent", JobPriority.HIGH) is False

    def test_get_statistics(self):
        queue = AutomationQueue()
        queue.enqueue(_make_job(job_id="a", priority=JobPriority.LOW))
        queue.enqueue(_make_job(job_id="b", priority=JobPriority.HIGH))
        stats = queue.get_statistics()
        assert stats.total == 2
        assert stats.by_priority.get("low") == 1
        assert stats.by_priority.get("high") == 1

    def test_clear(self):
        queue = AutomationQueue()
        queue.enqueue(_make_job())
        queue.enqueue(_make_job())
        queue.clear()
        assert queue.is_empty is True

    def test_size(self):
        queue = AutomationQueue()
        assert queue.size == 0
        queue.enqueue(_make_job())
        assert queue.size == 1

    def test_is_empty(self):
        queue = AutomationQueue()
        assert queue.is_empty is True
        queue.enqueue(_make_job())
        assert queue.is_empty is False

    def test_queue_full(self):
        queue = AutomationQueue(max_size=1)
        queue.enqueue(_make_job())
        with pytest.raises(QueueFullError):
            queue.enqueue(_make_job())

    def test_get_queue_filtered(self):
        queue = AutomationQueue()
        queue.enqueue(_make_job(job_id="a", priority=JobPriority.HIGH))
        queue.enqueue(_make_job(job_id="b", priority=JobPriority.LOW))
        items = queue.get_queue(priority=JobPriority.HIGH)
        assert len(items) == 1
        assert items[0].job_id == "a"

    def test_get_queue_all(self):
        queue = AutomationQueue()
        queue.enqueue(_make_job(job_id="a"))
        queue.enqueue(_make_job(job_id="b"))
        items = queue.get_queue()
        assert len(items) == 2

    def test_thread_safety(self):
        queue = AutomationQueue(max_size=5000)
        errors: list[Exception] = []

        def worker(n: int) -> None:
            try:
                for i in range(100):
                    job = _make_job(job_id=f"job-{n}-{i}")
                    queue.enqueue(job)
                    queue.peek()
            except Exception as e:
                errors.append(e)

        threads = [Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0


class TestExecutionHistory:
    def test_record_and_get(self):
        history = ExecutionHistory()
        record = ExecutionRecord(job_id="job-1")
        history.record(record)
        result = history.get(record.id)
        assert result is not None
        assert result.job_id == "job-1"

    def test_get_nonexistent(self):
        history = ExecutionHistory()
        assert history.get("nonexistent") is None

    def test_query_by_job_id(self):
        history = ExecutionHistory()
        r1 = ExecutionRecord(job_id="job-1", status=ExecutionStatus.COMPLETED,
                             started_at=datetime.utcnow())
        r2 = ExecutionRecord(job_id="job-2", status=ExecutionStatus.FAILED,
                             started_at=datetime.utcnow())
        history.record(r1)
        history.record(r2)
        results = history.query(HistoryQuery(job_id="job-1"))
        assert len(results) == 1
        assert results[0].job_id == "job-1"

    def test_query_by_status(self):
        history = ExecutionHistory()
        r1 = ExecutionRecord(job_id="job-1", status=ExecutionStatus.COMPLETED,
                             started_at=datetime.utcnow())
        r2 = ExecutionRecord(job_id="job-2", status=ExecutionStatus.FAILED,
                             started_at=datetime.utcnow())
        history.record(r1)
        history.record(r2)
        results = history.query(HistoryQuery(status=ExecutionStatus.FAILED))
        assert len(results) == 1
        assert results[0].status == ExecutionStatus.FAILED

    def test_query_limit(self):
        history = ExecutionHistory()
        for _ in range(10):
            history.record(ExecutionRecord(
                job_id="job-1", status=ExecutionStatus.COMPLETED,
                started_at=datetime.utcnow(),
            ))
        results = history.query(HistoryQuery(job_id="job-1", limit=5))
        assert len(results) == 5

    def test_query_offset(self):
        history = ExecutionHistory()
        for _ in range(10):
            history.record(ExecutionRecord(
                job_id="job-1", status=ExecutionStatus.COMPLETED,
                started_at=datetime.utcnow(),
            ))
        results = history.query(HistoryQuery(job_id="job-1", limit=10, offset=5))
        assert len(results) == 5

    def test_list_by_job(self):
        history = ExecutionHistory()
        r1 = ExecutionRecord(job_id="job-1", started_at=datetime.utcnow())
        r2 = ExecutionRecord(job_id="job-1", started_at=datetime.utcnow())
        history.record(r1)
        history.record(r2)
        results = history.list_by_job("job-1")
        assert len(results) == 2

    def test_clear(self):
        history = ExecutionHistory()
        history.record(ExecutionRecord(job_id="job-1"))
        history.clear()
        assert history.count() == 0

    def test_count(self):
        history = ExecutionHistory()
        assert history.count() == 0
        history.record(ExecutionRecord(job_id="job-1"))
        assert history.count() == 1


class TestPolicyEnforcer:
    def test_check_concurrent_jobs_under_limit(self):
        config = AutomationConfig(max_concurrent_jobs=5)
        enforcer = PolicyEnforcer(config)
        policy = AutomationPolicy()
        assert enforcer.check_concurrent_jobs(policy) is True

    def test_acquire_and_release_slot(self):
        config = AutomationConfig(max_concurrent_jobs=2)
        enforcer = PolicyEnforcer(config)
        assert enforcer.acquire_job_slot("job-1") is True
        assert enforcer.acquire_job_slot("job-2") is True
        assert enforcer.acquire_job_slot("job-3") is False
        enforcer.release_job_slot("job-1")
        assert enforcer.acquire_job_slot("job-3") is True

    def test_acquire_duplicate_slot(self):
        config = AutomationConfig(max_concurrent_jobs=5)
        enforcer = PolicyEnforcer(config)
        assert enforcer.acquire_job_slot("job-1") is True
        assert enforcer.acquire_job_slot("job-1") is False

    def test_release_nonexistent_slot(self):
        config = AutomationConfig(max_concurrent_jobs=5)
        enforcer = PolicyEnforcer(config)
        enforcer.release_job_slot("nonexistent")

    def test_is_in_quiet_hours_no_config(self):
        config = AutomationConfig()
        enforcer = PolicyEnforcer(config)
        policy = AutomationPolicy()
        assert enforcer.is_in_quiet_hours(policy) is False

    def test_is_in_quiet_hours_with_config(self):
        config = AutomationConfig(
            quiet_hours_start="22:00",
            quiet_hours_end="06:00",
        )
        enforcer = PolicyEnforcer(config)
        policy = AutomationPolicy()
        now = datetime.utcnow()
        now_mins = now.hour * 60 + now.minute
        start_mins = 22 * 60
        end_mins = 6 * 60
        if start_mins <= end_mins:
            expected = start_mins <= now_mins <= end_mins
        else:
            expected = now_mins >= start_mins or now_mins <= end_mins
        assert enforcer.is_in_quiet_hours(policy) == expected

    def test_rate_limit(self):
        config = AutomationConfig(rate_limit_per_minute=3)
        enforcer = PolicyEnforcer(config)
        policy = AutomationPolicy(rate_limit_per_minute=3)
        assert enforcer.check_rate_limit(policy) is True
        assert enforcer.check_rate_limit(policy) is True
        assert enforcer.check_rate_limit(policy) is True
        assert enforcer.check_rate_limit(policy) is False

    def test_should_auto_approve(self):
        config = AutomationConfig()
        enforcer = PolicyEnforcer(config)
        policy = AutomationPolicy(auto_approve_threshold=0.8)
        assert enforcer.should_auto_approve(policy, 0.9) is True
        assert enforcer.should_auto_approve(policy, 0.7) is False

    def test_should_auto_approve_no_threshold(self):
        config = AutomationConfig()
        enforcer = PolicyEnforcer(config)
        policy = AutomationPolicy()
        assert enforcer.should_auto_approve(policy, 0.9) is False

    def test_get_active_job_count(self):
        config = AutomationConfig(max_concurrent_jobs=5)
        enforcer = PolicyEnforcer(config)
        assert enforcer.get_active_job_count() == 0
        enforcer.acquire_job_slot("job-1")
        assert enforcer.get_active_job_count() == 1

    def test_reset(self):
        config = AutomationConfig(max_concurrent_jobs=5)
        enforcer = PolicyEnforcer(config)
        enforcer.acquire_job_slot("job-1")
        enforcer.check_rate_limit(AutomationPolicy())
        enforcer.reset()
        assert enforcer.get_active_job_count() == 0


class TestAutomationScheduler:
    def test_calculate_next_run_active_job(self):
        scheduler = AutomationScheduler()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.SCHEDULED,
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
        )
        job = _make_job(
            automation_type=AutomationType.ONE_TIME,
            trigger=trigger,
            state=JobState.ACTIVE,
            enabled=True,
        )
        result = scheduler.calculate_next_run(job)
        assert result is not None
        assert result == trigger.scheduled_at

    def test_calculate_next_run_disabled_job(self):
        scheduler = AutomationScheduler()
        job = _make_job(enabled=False, state=JobState.ACTIVE)
        result = scheduler.calculate_next_run(job)
        assert result is None

    def test_calculate_next_run_paused_job(self):
        scheduler = AutomationScheduler()
        job = _make_job(enabled=True, state=JobState.PAUSED)
        result = scheduler.calculate_next_run(job)
        assert result is None

    def test_calculate_next_run_manual_type(self):
        scheduler = AutomationScheduler()
        job = _make_job(automation_type=AutomationType.MANUAL)
        result = scheduler.calculate_next_run(job)
        assert result is None

    def test_is_eligible_true(self):
        scheduler = AutomationScheduler()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.SCHEDULED,
            scheduled_at=datetime.utcnow() - timedelta(seconds=1),
        )
        job = _make_job(
            automation_type=AutomationType.ONE_TIME,
            trigger=trigger,
            state=JobState.ACTIVE,
            enabled=True,
        )
        assert scheduler.is_eligible(job) is True

    def test_is_eligible_false_not_active(self):
        scheduler = AutomationScheduler()
        job = _make_job(enabled=True, state=JobState.PAUSED)
        assert scheduler.is_eligible(job) is False

    def test_is_eligible_false_not_enabled(self):
        scheduler = AutomationScheduler()
        job = _make_job(enabled=False, state=JobState.ACTIVE)
        assert scheduler.is_eligible(job) is False

    def test_is_eligible_false_manual(self):
        scheduler = AutomationScheduler()
        job = _make_job(automation_type=AutomationType.MANUAL)
        assert scheduler.is_eligible(job) is False

    def test_is_eligible_false_event_driven(self):
        scheduler = AutomationScheduler()
        job = _make_job(automation_type=AutomationType.EVENT_DRIVEN)
        assert scheduler.is_eligible(job) is False

    def test_get_recurring_intervals_daily(self):
        scheduler = AutomationScheduler()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.DAILY,
            daily_time="12:00",
        )
        job = _make_job(
            automation_type=AutomationType.RECURRING,
            trigger=trigger,
        )
        intervals = scheduler.get_recurring_intervals(job, count=3)
        assert len(intervals) == 3

    def test_get_recurring_intervals_weekly(self):
        scheduler = AutomationScheduler()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.WEEKLY,
            weekly_day=0,
            weekly_time="10:00",
        )
        job = _make_job(
            automation_type=AutomationType.RECURRING,
            trigger=trigger,
        )
        intervals = scheduler.get_recurring_intervals(job, count=2)
        assert len(intervals) == 2

    def test_get_recurring_intervals_one_time(self):
        scheduler = AutomationScheduler()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.SCHEDULED,
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
        )
        job = _make_job(
            automation_type=AutomationType.ONE_TIME,
            trigger=trigger,
        )
        intervals = scheduler.get_recurring_intervals(job, count=5)
        assert len(intervals) == 1

    def test_get_recurring_intervals_manual(self):
        scheduler = AutomationScheduler()
        job = _make_job(automation_type=AutomationType.MANUAL)
        intervals = scheduler.get_recurring_intervals(job)
        assert len(intervals) == 0


class TestAutomationService:
    def test_create_job(self):
        service = AutomationService()
        job = service.create_job(
            job_id="test-job",
            name="Test Job",
            target_module="jobs",
            target_action="search",
        )
        assert job.id == "test-job"
        assert job.name == "Test Job"
        assert job.target_module == "jobs"
        assert job.target_action == "search"
        assert job.state == JobState.ACTIVE

    def test_create_duplicate_job(self):
        service = AutomationService()
        service.create_job(
            job_id="dup-job",
            name="Original",
            target_module="jobs",
            target_action="search",
        )
        with pytest.raises(DuplicateJobError):
            service.create_job(
                job_id="dup-job",
                name="Duplicate",
                target_module="jobs",
                target_action="search",
            )

    def test_get_job(self):
        service = AutomationService()
        service.create_job(
            job_id="get-job",
            name="Get Test",
            target_module="jobs",
            target_action="search",
        )
        job = service.get_job("get-job")
        assert job is not None
        assert job.name == "Get Test"

    def test_get_job_not_found(self):
        service = AutomationService()
        assert service.get_job("nonexistent") is None

    def test_list_jobs(self):
        service = AutomationService()
        service.create_job(
            job_id="a", name="A", target_module="jobs", target_action="search",
            priority=JobPriority.HIGH,
        )
        service.create_job(
            job_id="b", name="B", target_module="jobs", target_action="search",
            priority=JobPriority.LOW,
        )
        jobs = service.list_jobs()
        assert len(jobs) == 2

    def test_pause_job(self):
        service = AutomationService()
        service.create_job(
            job_id="pause-test", name="Pause Test",
            target_module="jobs", target_action="search",
        )
        paused = service.pause_job("pause-test")
        assert paused.state == JobState.PAUSED

    def test_resume_job(self):
        service = AutomationService()
        service.create_job(
            job_id="resume-test", name="Resume Test",
            target_module="jobs", target_action="search",
        )
        service.pause_job("resume-test")
        resumed = service.resume_job("resume-test")
        assert resumed.state == JobState.ACTIVE

    def test_cancel_job(self):
        service = AutomationService()
        service.create_job(
            job_id="cancel-test", name="Cancel Test",
            target_module="jobs", target_action="search",
        )
        cancelled = service.cancel_job("cancel-test")
        assert cancelled.state == JobState.CANCELLED

    def test_cancel_already_cancelled(self):
        service = AutomationService()
        service.create_job(
            job_id="double-cancel", name="Double Cancel",
            target_module="jobs", target_action="search",
        )
        service.cancel_job("double-cancel")
        with pytest.raises(JobDisabledError):
            service.cancel_job("double-cancel")

    def test_delete_job(self):
        service = AutomationService()
        service.create_job(
            job_id="delete-me", name="Delete Me",
            target_module="jobs", target_action="search",
        )
        assert service.delete_job("delete-me") is True
        assert service.get_job("delete-me") is None

    def test_trigger_now(self):
        service = AutomationService()
        service.create_job(
            job_id="trigger-now", name="Trigger Now",
            target_module="jobs", target_action="search",
        )
        record = service.trigger_now("trigger-now")
        assert record.job_id == "trigger-now"
        assert record.status == ExecutionStatus.PENDING

    def test_trigger_now_disabled_job(self):
        service = AutomationService()
        service.create_job(
            job_id="disabled-job", name="Disabled",
            target_module="jobs", target_action="search",
            enabled=False,
        )
        with pytest.raises(JobDisabledError):
            service.trigger_now("disabled-job")

    def test_trigger_now_paused_job(self):
        service = AutomationService()
        service.create_job(
            job_id="paused-job", name="Paused",
            target_module="jobs", target_action="search",
        )
        service.pause_job("paused-job")
        with pytest.raises(JobPausedError):
            service.trigger_now("paused-job")

    def test_trigger_now_missing_target(self):
        validator = AutomationValidator()
        job = _make_job(job_id="no-target")
        job.target_module = ""
        job.target_action = ""
        with pytest.raises(MissingTargetError):
            validator.validate_execution(job)

    def test_record_execution_completed(self):
        service = AutomationService()
        service.create_job(
            job_id="exec-test", name="Exec Test",
            target_module="jobs", target_action="search",
        )
        record = service.record_execution(
            job_id="exec-test",
            status=ExecutionStatus.COMPLETED,
            duration_seconds=10.5,
        )
        assert record.status == ExecutionStatus.COMPLETED
        assert record.duration_seconds == 10.5

    def test_record_execution_failed(self):
        service = AutomationService()
        service.create_job(
            job_id="fail-test", name="Fail Test",
            target_module="jobs", target_action="search",
        )
        record = service.record_execution(
            job_id="fail-test",
            status=ExecutionStatus.FAILED,
            error="Something went wrong",
        )
        assert record.status == ExecutionStatus.FAILED
        assert record.error == "Something went wrong"

    def test_record_execution_retry_exhausted(self):
        service = AutomationService()
        service.create_job(
            job_id="retry-limit", name="Retry Limit",
            target_module="jobs", target_action="search",
        )
        for _ in range(2):
            service.record_execution("retry-limit", ExecutionStatus.FAILED)
        with pytest.raises(RetryLimitExceededError):
            service.record_execution("retry-limit", ExecutionStatus.FAILED)

    def test_list_history(self):
        service = AutomationService()
        service.create_job(
            job_id="history-job", name="History",
            target_module="jobs", target_action="search",
        )
        service.record_execution("history-job", ExecutionStatus.COMPLETED)
        service.record_execution("history-job", ExecutionStatus.FAILED)
        history = service.list_history(job_id="history-job")
        assert len(history) == 2

    def test_list_history_filter_by_status(self):
        service = AutomationService()
        service.create_job(
            job_id="filter-job", name="Filter",
            target_module="jobs", target_action="search",
        )
        service.record_execution("filter-job", ExecutionStatus.COMPLETED)
        service.record_execution("filter-job", ExecutionStatus.FAILED)
        completed = service.list_history(
            job_id="filter-job",
            status=ExecutionStatus.COMPLETED,
        )
        assert len(completed) == 1

    def test_pause_resume_queue(self):
        service = AutomationService()
        assert service.is_queue_paused() is False
        service.pause_queue()
        assert service.is_queue_paused() is True
        service.resume_queue()
        assert service.is_queue_paused() is False

    def test_queue_operations(self):
        service = AutomationService()
        service.create_job(
            job_id="q-job", name="Q",
            target_module="jobs", target_action="search",
        )
        service.trigger_now("q-job")
        queue = service.get_queue()
        assert len(queue) == 1
        stats = service.get_queue_statistics()
        assert stats.total == 1

    def test_get_active_job_count(self):
        service = AutomationService()
        assert service.get_active_job_count() == 0

    def test_cache_operations(self):
        service = AutomationService()
        service.create_job(
            job_id="cache-job", name="Cache",
            target_module="jobs", target_action="search",
        )
        assert service.get_job("cache-job") is not None
        service.invalidate_cache("cache-job")
        assert service.get_job("cache-job") is not None
        service.clear_cache()


class TestDeterminism:
    def test_same_input_same_output_create(self):
        s1 = AutomationService()
        s2 = AutomationService()
        j1 = s1.create_job(
            job_id="det-a", name="A",
            target_module="jobs", target_action="search",
        )
        j2 = s2.create_job(
            job_id="det-a", name="A",
            target_module="jobs", target_action="search",
        )
        assert j1.id == j2.id
        assert j1.name == j2.name
        assert j1.target_module == j2.target_module
        assert j1.target_action == j2.target_action
        assert j1.priority == j2.priority

    def test_priority_sorting_deterministic(self):
        q1 = AutomationQueue()
        q2 = AutomationQueue()
        jobs = [
            _make_job(job_id="a", priority=JobPriority.LOW),
            _make_job(job_id="b", priority=JobPriority.HIGH),
            _make_job(job_id="c", priority=JobPriority.MEDIUM),
        ]
        for j in jobs:
            q1.enqueue(j)
            q2.enqueue(j)
        while not q1.is_empty and not q2.is_empty:
            i1 = q1.dequeue()
            i2 = q2.dequeue()
            assert i1.job_id == i2.job_id


class TestEdgeCases:
    def test_empty_job_id(self):
        service = AutomationService()
        job = service.create_job(
            job_id="", name="Empty ID",
            target_module="jobs", target_action="search",
        )
        assert job.id == ""

    def test_very_long_name(self):
        service = AutomationService()
        long_name = "x" * 1000
        job = service.create_job(
            job_id="long-name", name=long_name,
            target_module="jobs", target_action="search",
        )
        assert job.name == long_name

    def test_special_chars_in_job_id(self):
        service = AutomationService()
        job_id = "job@#$%^&*()"
        job = service.create_job(
            job_id=job_id, name="Special",
            target_module="jobs", target_action="search",
        )
        assert job.id == job_id

    def test_unicode_in_name(self):
        service = AutomationService()
        name = "João 自动化 test"
        job = service.create_job(
            job_id="unicode-job", name=name,
            target_module="jobs", target_action="search",
        )
        assert job.name == name

    def test_zero_retries(self):
        service = AutomationService()
        policy = AutomationPolicy(max_retries=0)
        service.create_job(
            job_id="zero-retry", name="Zero Retry",
            target_module="jobs", target_action="search",
            policy=policy,
        )
        with pytest.raises(RetryLimitExceededError):
            service.record_execution("zero-retry", ExecutionStatus.FAILED)

    def test_negative_priority_not_allowed(self):
        p = JobPriority.LOW.value
        assert p >= 0

    def test_max_queue_size(self):
        queue = AutomationQueue(max_size=0)
        with pytest.raises(QueueFullError):
            queue.enqueue(_make_job())

    def test_future_scheduled_trigger_not_due(self):
        evaluator = TriggerEvaluator()
        trigger = AutomationTrigger(
            trigger_type=TriggerType.SCHEDULED,
            scheduled_at=datetime.utcnow() + timedelta(days=365),
        )
        assert evaluator.evaluate(trigger) is False

    def test_update_job_with_new_trigger(self):
        service = AutomationService()
        service.create_job(
            job_id="update-trigger", name="Update Trigger",
            target_module="jobs", target_action="search",
        )
        job = service.get_job("update-trigger")
        job.trigger = AutomationTrigger(
            trigger_type=TriggerType.DAILY,
            daily_time="06:00",
        )
        updated = service.update_job(job)
        assert updated.trigger.trigger_type == TriggerType.DAILY
        assert updated.trigger.daily_time == "06:00"

    def test_history_max_records(self):
        history = ExecutionHistory(max_records=5)
        for i in range(10):
            history.record(ExecutionRecord(
                job_id=f"job-{i}",
                started_at=datetime.utcnow(),
            ))
        assert history.count() == 5


class TestThreadSafety:
    def test_queue_concurrent_enqueue_dequeue(self):
        queue = AutomationQueue(max_size=5000)
        errors: list[Exception] = []

        def producer(n: int) -> None:
            try:
                for i in range(50):
                    queue.enqueue(_make_job(job_id=f"prod-{n}-{i}"))
            except Exception as e:
                errors.append(e)

        def consumer() -> None:
            try:
                for _ in range(25):
                    queue.dequeue()
            except Exception as e:
                errors.append(e)

        threads = ([Thread(target=producer, args=(i,)) for i in range(4)]
                   + [Thread(target=consumer) for _ in range(4)])
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_history_concurrent_record(self):
        history = ExecutionHistory()
        errors: list[Exception] = []

        def worker(n: int) -> None:
            try:
                for i in range(100):
                    history.record(ExecutionRecord(
                        job_id=f"job-{n}-{i}",
                        started_at=datetime.utcnow(),
                    ))
            except Exception as e:
                errors.append(e)

        threads = [Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0

    def test_policy_enforcer_concurrent(self):
        config = AutomationConfig(max_concurrent_jobs=50)
        enforcer = PolicyEnforcer(config)
        errors: list[Exception] = []

        def worker(n: int) -> None:
            try:
                for i in range(20):
                    job_id = f"job-{n}-{i}"
                    if enforcer.acquire_job_slot(job_id):
                        enforcer.release_job_slot(job_id)
            except Exception as e:
                errors.append(e)

        threads = [Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0


class TestFullLifecycle:
    def test_job_lifecycle(self):
        service = AutomationService()
        job = service.create_job(
            job_id="lifecycle", name="Lifecycle",
            target_module="jobs", target_action="search",
        )
        assert job.state == JobState.ACTIVE
        service.pause_job("lifecycle")
        assert service.get_job("lifecycle").state == JobState.PAUSED
        service.resume_job("lifecycle")
        assert service.get_job("lifecycle").state == JobState.ACTIVE
        trigger = AutomationTrigger(
            trigger_type=TriggerType.SCHEDULED,
            scheduled_at=datetime.utcnow() - timedelta(seconds=1),
        )
        job.trigger = trigger
        service.update_job(job)
        record = service.trigger_now("lifecycle")
        assert record.status == ExecutionStatus.PENDING
        exec_record = service.record_execution("lifecycle", ExecutionStatus.COMPLETED)
        assert exec_record.status == ExecutionStatus.COMPLETED
        history = service.list_history(job_id="lifecycle")
        assert len(history) == 1

    def test_full_queue_lifecycle(self):
        queue = AutomationQueue()
        assert queue.is_empty is True
        job = _make_job(job_id="full-q")
        queue.enqueue(job)
        assert queue.is_empty is False
        queue.pause()
        assert queue.is_paused() is True
        assert queue.dequeue() is None
        queue.resume()
        assert queue.dequeue() is not None
        assert queue.is_empty is True
