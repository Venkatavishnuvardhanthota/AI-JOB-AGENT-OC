from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest

from app.application_tracking.cache import TrackingCache
from app.application_tracking.config import ApplicationTrackingConfig
from app.application_tracking.exceptions import (
    ApplicationNotFoundError,
    CorruptedHistoryError,
    DuplicateApplicationError,
    InvalidArchiveStateError,
    InvalidStatusTransitionError,
)
from app.application_tracking.metrics import MetricsCalculator
from app.application_tracking.schemas import (
    ApplicationMetrics,
    ApplicationRecord,
    ApplicationStatus,
    TimelineEvent,
    TimelineEventType,
)
from app.application_tracking.service import ApplicationTrackingService
from app.application_tracking.status import StatusManager
from app.application_tracking.timeline import TimelineManager
from app.application_tracking.tracker import ApplicationTracker
from app.application_tracking.validator import ApplicationTrackingValidator
from app.workflow.schemas import WorkflowState


class TestApplicationStatus:
    def test_all_statuses_defined(self):
        expected = [
            "draft", "ready", "queued", "submitted", "viewed",
            "in_review", "assessment", "interview", "offer",
            "hired", "rejected", "withdrawn", "archived",
        ]
        values = [s.value for s in ApplicationStatus]
        for exp in expected:
            assert exp in values

    def test_all_statuses_unique(self):
        values = [s.value for s in ApplicationStatus]
        assert len(values) == len(set(values))

    def test_draft_is_default(self):
        record = ApplicationRecord(application_id="test")
        assert record.current_status == ApplicationStatus.DRAFT


class TestApplicationTrackingConfig:
    def test_default_config(self):
        config = ApplicationTrackingConfig()
        assert config.cache_ttl_seconds == 300
        assert config.strict_validation is True
        assert config.track_timeline is True
        assert config.auto_calculate_metrics is True
        assert config.max_timeline_events == 1000

    def test_custom_config(self):
        config = ApplicationTrackingConfig(
            cache_ttl_seconds=600,
            strict_validation=False,
            track_timeline=False,
            auto_calculate_metrics=False,
            max_timeline_events=500,
        )
        assert config.cache_ttl_seconds == 600
        assert config.strict_validation is False
        assert config.track_timeline is False
        assert config.auto_calculate_metrics is False
        assert config.max_timeline_events == 500


class TestValidator:
    def test_validate_create_new(self):
        validator = ApplicationTrackingValidator()
        validator.validate_create("new-id", None)

    def test_validate_create_duplicate(self):
        validator = ApplicationTrackingValidator()
        existing = ApplicationRecord(application_id="existing")
        with pytest.raises(DuplicateApplicationError):
            validator.validate_create("existing", existing)

    def test_validate_get_exists(self):
        validator = ApplicationTrackingValidator()
        record = ApplicationRecord(application_id="test")
        result = validator.validate_get(record)
        assert result.application_id == "test"

    def test_validate_get_none(self):
        validator = ApplicationTrackingValidator()
        with pytest.raises(ApplicationNotFoundError):
            validator.validate_get(None)

    def test_validate_get_deleted(self):
        validator = ApplicationTrackingValidator()
        record = ApplicationRecord(application_id="test", deleted=True)
        with pytest.raises(ApplicationNotFoundError):
            validator.validate_get(record)

    def test_validate_status_update_valid(self):
        validator = ApplicationTrackingValidator()
        record = ApplicationRecord(application_id="test")
        validator.validate_status_update(record, ApplicationStatus.READY)

    def test_validate_status_update_invalid(self):
        validator = ApplicationTrackingValidator()
        record = ApplicationRecord(application_id="test")
        with pytest.raises(InvalidStatusTransitionError):
            validator.validate_status_update(record, ApplicationStatus.SUBMITTED)

    def test_validate_status_update_from_hired(self):
        validator = ApplicationTrackingValidator()
        record = ApplicationRecord(
            application_id="test", current_status=ApplicationStatus.HIRED
        )
        validator.validate_status_update(record, ApplicationStatus.ARCHIVED)

    def test_validate_status_update_from_hired_invalid(self):
        validator = ApplicationTrackingValidator()
        record = ApplicationRecord(
            application_id="test", current_status=ApplicationStatus.HIRED
        )
        with pytest.raises(InvalidStatusTransitionError):
            validator.validate_status_update(record, ApplicationStatus.DRAFT)

    def test_validate_archive_not_archived(self):
        validator = ApplicationTrackingValidator()
        record = ApplicationRecord(application_id="test")
        validator.validate_archive(record)

    def test_validate_archive_already_archived(self):
        validator = ApplicationTrackingValidator()
        record = ApplicationRecord(application_id="test", archived=True)
        with pytest.raises(InvalidArchiveStateError):
            validator.validate_archive(record)

    def test_validate_restore_archived(self):
        validator = ApplicationTrackingValidator()
        record = ApplicationRecord(application_id="test", archived=True)
        validator.validate_restore(record)

    def test_validate_restore_not_archived(self):
        validator = ApplicationTrackingValidator()
        record = ApplicationRecord(application_id="test")
        with pytest.raises(InvalidArchiveStateError):
            validator.validate_restore(record)

    def test_validate_delete_found(self):
        validator = ApplicationTrackingValidator()
        record = ApplicationRecord(application_id="test")
        result = validator.validate_delete(record)
        assert result.application_id == "test"

    def test_validate_delete_not_found(self):
        validator = ApplicationTrackingValidator()
        with pytest.raises(ApplicationNotFoundError):
            validator.validate_delete(None)

    def test_validate_history_chronological(self):
        validator = ApplicationTrackingValidator()
        record = ApplicationRecord(application_id="test")
        record.timeline = [
            TimelineEvent(
                event_type="a", timestamp=datetime(2024, 1, 1)
            ),
            TimelineEvent(
                event_type="b", timestamp=datetime(2024, 1, 2)
            ),
        ]
        validator.validate_history(record)

    def test_validate_history_non_chronological(self):
        validator = ApplicationTrackingValidator()
        record = ApplicationRecord(application_id="test")
        record.timeline = [
            TimelineEvent(
                event_type="a", timestamp=datetime(2024, 1, 3)
            ),
            TimelineEvent(
                event_type="b", timestamp=datetime(2024, 1, 1)
            ),
        ]
        with pytest.raises(CorruptedHistoryError):
            validator.validate_history(record)

    def test_validate_history_not_strict(self):
        validator = ApplicationTrackingValidator(strict=False)
        record = ApplicationRecord(application_id="test")
        record.timeline = [
            TimelineEvent(
                event_type="a", timestamp=datetime(2024, 1, 3)
            ),
            TimelineEvent(
                event_type="b", timestamp=datetime(2024, 1, 1)
            ),
        ]
        validator.validate_history(record)

    def test_get_allowed_statuses_draft(self):
        allowed = ApplicationTrackingValidator._get_allowed_statuses(
            ApplicationStatus.DRAFT
        )
        assert ApplicationStatus.READY in allowed
        assert ApplicationStatus.WITHDRAWN in allowed
        assert ApplicationStatus.ARCHIVED in allowed
        assert ApplicationStatus.SUBMITTED not in allowed

    def test_get_allowed_statuses_submitted(self):
        allowed = ApplicationTrackingValidator._get_allowed_statuses(
            ApplicationStatus.SUBMITTED
        )
        assert ApplicationStatus.VIEWED in allowed
        assert ApplicationStatus.IN_REVIEW in allowed
        assert ApplicationStatus.INTERVIEW in allowed
        assert ApplicationStatus.OFFER in allowed
        assert ApplicationStatus.REJECTED in allowed
        assert ApplicationStatus.WITHDRAWN in allowed

    def test_get_allowed_statuses_archived(self):
        allowed = ApplicationTrackingValidator._get_allowed_statuses(
            ApplicationStatus.ARCHIVED
        )
        assert allowed == []


class TestTimelineManager:
    def test_add_event(self):
        tl = TimelineManager()
        record = ApplicationRecord(application_id="test")
        event = tl.add_event(record, TimelineEventType.APPLICATION_CREATED)
        assert len(record.timeline) == 1
        assert record.timeline[0].event_type == TimelineEventType.APPLICATION_CREATED
        assert event.id is not None

    def test_add_event_with_actor_and_reason(self):
        tl = TimelineManager()
        record = ApplicationRecord(application_id="test")
        tl.add_event(
            record,
            TimelineEventType.SUBMITTED,
            actor="user1",
            reason="Completed application",
        )
        assert record.timeline[0].actor == "user1"
        assert record.timeline[0].reason == "Completed application"

    def test_add_status_event(self):
        tl = TimelineManager()
        record = ApplicationRecord(application_id="test")
        event = tl.add_status_event(record, ApplicationStatus.READY)
        assert event.metadata["new_status"] == "ready"
        assert event.metadata["previous_status"] == "draft"

    def test_add_workflow_event(self):
        tl = TimelineManager()
        record = ApplicationRecord(application_id="test")
        event = tl.add_workflow_event(record, WorkflowState.MATCHED)
        assert event.metadata["workflow_state"] == "matched"
        assert event.event_type == TimelineEventType.WORKFLOW_EVENT

    def test_get_timeline_forward(self):
        tl = TimelineManager()
        record = ApplicationRecord(application_id="test")
        tl.add_event(record, "a")
        tl.add_event(record, "b")
        events = tl.get_timeline(record)
        assert len(events) == 2
        assert events[0].event_type == "a"
        assert events[1].event_type == "b"

    def test_get_timeline_reverse(self):
        tl = TimelineManager()
        record = ApplicationRecord(application_id="test")
        tl.add_event(record, "a")
        tl.add_event(record, "b")
        events = tl.get_timeline(record, reverse=True)
        assert events[0].event_type == "b"
        assert events[1].event_type == "a"

    def test_get_events_by_type(self):
        tl = TimelineManager()
        record = ApplicationRecord(application_id="test")
        tl.add_event(record, "type_a")
        tl.add_event(record, "type_b")
        tl.add_event(record, "type_a")
        events = tl.get_events_by_type(record, "type_a")
        assert len(events) == 2

    def test_status_to_event_type_mapping(self):
        assert TimelineManager._status_to_event_type(
            ApplicationStatus.DRAFT
        ) == TimelineEventType.APPLICATION_CREATED
        assert TimelineManager._status_to_event_type(
            ApplicationStatus.SUBMITTED
        ) == TimelineEventType.SUBMITTED
        assert TimelineManager._status_to_event_type(
            ApplicationStatus.REJECTED
        ) == TimelineEventType.REJECTED


class TestStatusManager:
    def test_update_status(self):
        validator = ApplicationTrackingValidator()
        timeline = TimelineManager()
        sm = StatusManager(validator, timeline)
        record = ApplicationRecord(application_id="test")
        result = sm.update_status(record, ApplicationStatus.READY)
        assert result.current_status == ApplicationStatus.READY
        assert len(result.timeline) == 1

    def test_update_status_same_state_noop(self):
        validator = ApplicationTrackingValidator()
        timeline = TimelineManager()
        sm = StatusManager(validator, timeline)
        record = ApplicationRecord(
            application_id="test", current_status=ApplicationStatus.READY
        )
        result = sm.update_status(record, ApplicationStatus.READY)
        assert result.current_status == ApplicationStatus.READY
        assert len(result.timeline) == 0

    def test_update_status_invalid(self):
        validator = ApplicationTrackingValidator()
        timeline = TimelineManager()
        sm = StatusManager(validator, timeline)
        record = ApplicationRecord(application_id="test")
        with pytest.raises(InvalidStatusTransitionError):
            sm.update_status(record, ApplicationStatus.SUBMITTED)

    def test_update_status_sets_submission_timestamp(self):
        validator = ApplicationTrackingValidator()
        timeline = TimelineManager()
        sm = StatusManager(validator, timeline)
        record = ApplicationRecord(application_id="test")
        sm.update_status(record, ApplicationStatus.READY)
        sm.update_status(record, ApplicationStatus.QUEUED)
        sm.update_status(record, ApplicationStatus.SUBMITTED)
        assert record.submission_timestamp is not None

    def test_update_status_does_not_overwrite_submission_timestamp(self):
        validator = ApplicationTrackingValidator()
        timeline = TimelineManager()
        sm = StatusManager(validator, timeline)
        record = ApplicationRecord(application_id="test")
        sm.update_status(record, ApplicationStatus.READY)
        sm.update_status(record, ApplicationStatus.QUEUED)
        sm.update_status(record, ApplicationStatus.SUBMITTED)
        ts = record.submission_timestamp
        sm.update_status(record, ApplicationStatus.VIEWED)
        assert record.submission_timestamp == ts
        assert record.current_status == ApplicationStatus.VIEWED

    def test_update_status_increments_counter(self):
        validator = ApplicationTrackingValidator()
        timeline = TimelineManager()
        sm = StatusManager(validator, timeline)
        record = ApplicationRecord(application_id="test")
        sm.update_status(record, ApplicationStatus.READY)
        assert record.metrics.status_change_count == 1
        sm.update_status(record, ApplicationStatus.QUEUED)
        assert record.metrics.status_change_count == 2

    def test_update_status_counts_interviews(self):
        validator = ApplicationTrackingValidator()
        timeline = TimelineManager()
        sm = StatusManager(validator, timeline)
        record = ApplicationRecord(application_id="test")
        sm.update_status(record, ApplicationStatus.READY)
        sm.update_status(record, ApplicationStatus.QUEUED)
        sm.update_status(record, ApplicationStatus.SUBMITTED)
        sm.update_status(record, ApplicationStatus.INTERVIEW)
        assert record.metrics.number_of_interviews == 1
        sm.update_status(record, ApplicationStatus.INTERVIEW)
        assert record.metrics.number_of_interviews == 1

    def test_update_status_counts_offers_and_rejections(self):
        validator = ApplicationTrackingValidator()
        timeline = TimelineManager()
        sm = StatusManager(validator, timeline)
        record = ApplicationRecord(application_id="test")
        sm.update_status(record, ApplicationStatus.READY)
        sm.update_status(record, ApplicationStatus.QUEUED)
        sm.update_status(record, ApplicationStatus.SUBMITTED)
        sm.update_status(record, ApplicationStatus.INTERVIEW)
        sm.update_status(record, ApplicationStatus.OFFER)
        assert record.metrics.offer_count == 1
        sm.update_status(record, ApplicationStatus.REJECTED)
        assert record.metrics.rejection_count == 1
        assert record.metrics.offer_count == 1

    def test_update_status_counts_withdrawals(self):
        validator = ApplicationTrackingValidator()
        timeline = TimelineManager()
        sm = StatusManager(validator, timeline)
        record = ApplicationRecord(application_id="test")
        sm.update_status(record, ApplicationStatus.WITHDRAWN)
        assert record.metrics.withdrawal_count == 1

    def test_no_timeline_when_disabled(self):
        config = ApplicationTrackingConfig(track_timeline=False)
        validator = ApplicationTrackingValidator()
        timeline = TimelineManager()
        sm = StatusManager(validator, timeline, config)
        record = ApplicationRecord(application_id="test")
        sm.update_status(record, ApplicationStatus.READY)
        assert len(record.timeline) == 0


class TestMetricsCalculator:
    def test_calculate_defaults(self):
        calc = MetricsCalculator()
        record = ApplicationRecord(application_id="test")
        metrics = calc.calculate(record)
        assert metrics.days_since_submission is None
        assert metrics.timeline_event_count == 0
        assert metrics.total_lifecycle_duration_hours == 0.0

    def test_calculate_with_submission(self):
        calc = MetricsCalculator()
        record = ApplicationRecord(
            application_id="test",
            submission_timestamp=datetime.utcnow() - timedelta(days=5),
        )
        metrics = calc.calculate(record)
        assert metrics.days_since_submission == 5

    def test_calculate_with_timeline(self):
        calc = MetricsCalculator()
        record = ApplicationRecord(
            application_id="test",
            timeline=[
                TimelineEvent(
                    event_type="created",
                    timestamp=datetime.utcnow() - timedelta(hours=48),
                ),
            ],
        )
        metrics = calc.calculate(record)
        assert metrics.timeline_event_count == 1
        assert metrics.total_lifecycle_duration_hours > 0

    def test_refresh_updates_record(self):
        calc = MetricsCalculator()
        record = ApplicationRecord(
            application_id="test",
            submission_timestamp=datetime.utcnow() - timedelta(days=1),
        )
        calc.refresh(record)
        assert record.metrics.days_since_submission == 1

    def test_calculate_time_in_status_no_timeline(self):
        calc = MetricsCalculator()
        record = ApplicationRecord(application_id="test")
        hours = calc._calculate_time_in_status(record, datetime.utcnow())
        assert hours == 0.0

    def test_calculate_time_in_status_with_timeline(self):
        calc = MetricsCalculator()
        record = ApplicationRecord(application_id="test")
        record.timeline = [
            TimelineEvent(
                event_type="created",
                timestamp=datetime.utcnow() - timedelta(hours=24),
            ),
        ]
        hours = calc._calculate_time_in_status(record, datetime.utcnow())
        assert hours > 0


class TestApplicationTracker:
    def test_create(self):
        tracker = ApplicationTracker()
        record = tracker.create("app-1")
        assert record.application_id == "app-1"
        assert record.current_status == ApplicationStatus.DRAFT
        assert len(record.timeline) == 1

    def test_create_duplicate(self):
        tracker = ApplicationTracker()
        existing = ApplicationRecord(application_id="app-1")
        with pytest.raises(DuplicateApplicationError):
            tracker.create("app-1", existing)

    def test_update_status(self):
        tracker = ApplicationTracker()
        record = tracker.create("app-1")
        result = tracker.update_status(record, ApplicationStatus.READY)
        assert result.current_status == ApplicationStatus.READY

    def test_record_workflow_event(self):
        tracker = ApplicationTracker()
        record = tracker.create("app-1")
        result = tracker.record_workflow_event(
            record, WorkflowState.MATCHED, actor="system"
        )
        assert result.workflow_state == WorkflowState.MATCHED
        assert len(result.timeline) == 2

    def test_add_event(self):
        tracker = ApplicationTracker()
        record = tracker.create("app-1")
        event = tracker.add_event(record, TimelineEventType.NOTE_ADDED)
        assert event.event_type == TimelineEventType.NOTE_ADDED
        assert len(record.timeline) == 2

    def test_get_timeline(self):
        tracker = ApplicationTracker()
        record = tracker.create("app-1")
        events = tracker.get_timeline(record)
        assert len(events) == 1

    def test_get_timeline_reverse(self):
        tracker = ApplicationTracker()
        record = tracker.create("app-1")
        tracker.add_event(record, "second")
        events = tracker.get_timeline(record, reverse=True)
        assert events[0].event_type == "second"

    def test_get_metrics(self):
        tracker = ApplicationTracker()
        record = tracker.create("app-1")
        result = tracker.get_metrics(record)
        assert result.metrics.timeline_event_count == 1

    def test_archive(self):
        tracker = ApplicationTracker()
        record = tracker.create("app-1")
        result = tracker.archive(record)
        assert result.archived is True
        assert result.archived_at is not None

    def test_archive_already_archived(self):
        tracker = ApplicationTracker()
        record = tracker.create("app-1")
        tracker.archive(record)
        with pytest.raises(InvalidArchiveStateError):
            tracker.archive(record)

    def test_restore(self):
        tracker = ApplicationTracker()
        record = tracker.create("app-1")
        tracker.archive(record)
        result = tracker.restore(record)
        assert result.archived is False
        assert result.archived_at is None

    def test_restore_not_archived(self):
        tracker = ApplicationTracker()
        record = tracker.create("app-1")
        with pytest.raises(InvalidArchiveStateError):
            tracker.restore(record)

    def test_delete(self):
        tracker = ApplicationTracker()
        record = tracker.create("app-1")
        tracker.delete(record)
        assert record.deleted is True

    def test_validate_history_ok(self):
        tracker = ApplicationTracker()
        record = tracker.create("app-1")
        tracker.validate_history(record)

    def test_validate_history_non_chronological(self):
        tracker = ApplicationTracker()
        record = tracker.create("app-1")
        record.timeline.append(
            TimelineEvent(
                event_type="late",
                timestamp=datetime(2023, 1, 1),
            )
        )
        with pytest.raises(CorruptedHistoryError):
            tracker.validate_history(record)


class TestTrackingCache:
    def test_set_and_get(self):
        config = ApplicationTrackingConfig(cache_ttl_seconds=300)
        cache = TrackingCache(config)
        record = ApplicationRecord(application_id="test")
        cache.set("k1", record)
        result = cache.get("k1")
        assert result is not None
        assert result.application_id == "test"

    def test_get_missing(self):
        config = ApplicationTrackingConfig()
        cache = TrackingCache(config)
        assert cache.get("nonexistent") is None

    def test_invalidate(self):
        config = ApplicationTrackingConfig()
        cache = TrackingCache(config)
        record = ApplicationRecord(application_id="test")
        cache.set("k1", record)
        cache.invalidate("k1")
        assert cache.get("k1") is None

    def test_clear(self):
        config = ApplicationTrackingConfig()
        cache = TrackingCache(config)
        cache.set("k1", ApplicationRecord(application_id="t1"))
        cache.set("k2", ApplicationRecord(application_id="t2"))
        cache.clear()
        assert cache.get("k1") is None
        assert cache.get("k2") is None

    def test_ttl_expiry(self):
        config = ApplicationTrackingConfig(cache_ttl_seconds=0)
        cache = TrackingCache(config)
        record = ApplicationRecord(application_id="test")
        cache.set("k1", record)
        import time
        time.sleep(0.01)
        result = cache.get("k1")
        assert result is None

    def test_thread_safety(self):
        config = ApplicationTrackingConfig()
        cache = TrackingCache(config)
        import threading
        errors = []

        def worker(ident: str):
            try:
                for i in range(100):
                    key = f"{ident}-{i}"
                    cache.set(key, ApplicationRecord(application_id=key))
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


class TestApplicationTrackingService:
    def test_create(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        record = service.create(app_id)
        assert record.application_id == app_id
        assert record.current_status == ApplicationStatus.DRAFT

    def test_create_with_metadata(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        record = service.create(app_id, metadata={"source": "linkedin"})
        assert record.metadata["source"] == "linkedin"

    def test_get(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        record = service.get(app_id)
        assert record is not None
        assert record.application_id == app_id

    def test_get_nonexistent(self):
        service = ApplicationTrackingService()
        assert service.get("nonexistent") is None

    def test_update_status(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        result = service.update_status(app_id, ApplicationStatus.READY)
        assert result.current_status == ApplicationStatus.READY

    def test_update_status_invalid(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        with pytest.raises(InvalidStatusTransitionError):
            service.update_status(app_id, ApplicationStatus.SUBMITTED)

    def test_record_workflow_event(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        result = service.record_workflow_event(app_id, WorkflowState.MATCHED)
        assert result.workflow_state == WorkflowState.MATCHED

    def test_add_event(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        event = service.add_event(app_id, TimelineEventType.NOTE_ADDED)
        assert event.event_type == TimelineEventType.NOTE_ADDED

    def test_get_history(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        service.update_status(app_id, ApplicationStatus.READY)
        history = service.get_history(app_id)
        assert len(history) == 2

    def test_get_history_nonexistent(self):
        service = ApplicationTrackingService()
        assert service.get_history("nonexistent") == []

    def test_get_metrics(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        result = service.get_metrics(app_id)
        assert result is not None
        assert result.metrics.timeline_event_count == 1

    def test_get_metrics_nonexistent(self):
        service = ApplicationTrackingService()
        assert service.get_metrics("nonexistent") is None

    def test_archive(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        result = service.archive(app_id)
        assert result.archived is True

    def test_restore(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        service.archive(app_id)
        result = service.restore(app_id)
        assert result.archived is False

    def test_delete(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        service.delete(app_id)
        record = service.get(app_id)
        assert record is not None
        assert record.deleted is True

    def test_invalidate_cache(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        service.invalidate_cache(app_id)
        assert service.get(app_id) is None

    def test_clear_cache(self):
        service = ApplicationTrackingService()
        app_id1 = str(uuid.uuid4())
        app_id2 = str(uuid.uuid4())
        service.create(app_id1)
        service.create(app_id2)
        service.clear_cache()
        assert service.get(app_id1) is None
        assert service.get(app_id2) is None

    def test_full_lifecycle(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        service.record_workflow_event(app_id, WorkflowState.MATCHED)
        service.record_workflow_event(app_id, WorkflowState.PACKAGE_GENERATED)
        service.record_workflow_event(app_id, WorkflowState.READY_FOR_REVIEW)
        service.record_workflow_event(app_id, WorkflowState.APPROVED)
        service.update_status(app_id, ApplicationStatus.READY)
        service.update_status(app_id, ApplicationStatus.QUEUED)
        service.update_status(app_id, ApplicationStatus.SUBMITTED)
        service.record_workflow_event(app_id, WorkflowState.TRACKING)
        service.update_status(app_id, ApplicationStatus.VIEWED)
        service.update_status(app_id, ApplicationStatus.IN_REVIEW)
        service.update_status(app_id, ApplicationStatus.INTERVIEW)
        service.update_status(app_id, ApplicationStatus.OFFER)
        record = service.get(app_id)
        assert record is not None
        assert record.current_status == ApplicationStatus.OFFER
        assert len(record.timeline) >= 12

    def test_deterministic_behavior(self):
        service = ApplicationTrackingService()
        app_id1 = str(uuid.uuid4())
        app_id2 = str(uuid.uuid4())
        service.create(app_id1)
        service.create(app_id2)
        service.update_status(app_id1, ApplicationStatus.READY)
        service.update_status(app_id1, ApplicationStatus.QUEUED)
        service.update_status(app_id2, ApplicationStatus.READY)
        service.update_status(app_id2, ApplicationStatus.QUEUED)
        s1 = service.get(app_id1)
        s2 = service.get(app_id2)
        assert s1 is not None and s2 is not None
        assert s1.current_status == s2.current_status
        assert len(s1.timeline) == len(s2.timeline)

    def test_update_status_with_reason(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        service.update_status(
            app_id, ApplicationStatus.READY, reason="All checks passed"
        )
        history = service.get_history(app_id)
        assert history[-1].reason == "All checks passed"

    def test_record_workflow_event_with_actor(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.record_workflow_event(
            app_id, WorkflowState.MATCHED, actor="workflow_engine"
        )
        history = service.get_history(app_id)
        assert history[-1].actor == "workflow_engine"

    def test_add_event_with_metadata(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        event = service.add_event(
            app_id,
            TimelineEventType.NOTE_ADDED,
            metadata={"note": "Follow up needed"},
        )
        assert event.metadata["note"] == "Follow up needed"

    def test_archive_with_reason(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        service.archive(app_id, reason="Position filled")
        history = service.get_history(app_id)
        archive_events = [
            e for e in history if e.event_type == TimelineEventType.ARCHIVED
        ]
        assert len(archive_events) == 1
        assert archive_events[0].reason == "Position filled"


class TestSerialization:
    def test_application_record_serialization(self):
        record = ApplicationRecord(
            application_id="test",
            current_status=ApplicationStatus.SUBMITTED,
        )
        data = record.model_dump()
        assert data["application_id"] == "test"
        assert data["current_status"] == "submitted"
        assert data["archived"] is False

    def test_timeline_event_serialization(self):
        event = TimelineEvent(
            event_type=TimelineEventType.APPLICATION_CREATED,
            actor="system",
        )
        data = event.model_dump()
        assert data["event_type"] == "application_created"
        assert data["actor"] == "system"

    def test_timeline_event_with_metadata_serialization(self):
        event = TimelineEvent(
            event_type="custom_event",
            metadata={"key": "value"},
        )
        data = event.model_dump()
        assert data["event_type"] == "custom_event"
        assert data["metadata"]["key"] == "value"

    def test_application_metrics_serialization(self):
        metrics = ApplicationMetrics(
            days_since_submission=5,
            number_of_interviews=2,
            offer_count=1,
            rejection_count=0,
        )
        data = metrics.model_dump()
        assert data["days_since_submission"] == 5
        assert data["number_of_interviews"] == 2
        assert data["offer_count"] == 1

    def test_application_record_with_timeline_serialization(self):
        record = ApplicationRecord(
            application_id="test",
            timeline=[
                TimelineEvent(event_type="a", timestamp=datetime(2024, 1, 1)),
                TimelineEvent(event_type="b", timestamp=datetime(2024, 1, 2)),
            ],
        )
        data = record.model_dump()
        assert len(data["timeline"]) == 2
        assert data["timeline"][0]["event_type"] == "a"


class TestEdgeCases:
    def test_create_no_timeline_when_disabled(self):
        config = ApplicationTrackingConfig(track_timeline=False)
        tracker = ApplicationTracker(config)
        record = tracker.create("app-1")
        assert len(record.timeline) == 0

    def test_create_no_metrics_when_disabled(self):
        config = ApplicationTrackingConfig(auto_calculate_metrics=False)
        tracker = ApplicationTracker(config)
        record = tracker.create("app-1")
        assert record.metrics.timeline_event_count == 0

    def test_empty_timeline_no_error(self):
        service = ApplicationTrackingService()
        assert service.get_history("nonexistent") == []

    def test_draft_to_withdrawn(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        result = service.update_status(app_id, ApplicationStatus.WITHDRAWN)
        assert result.current_status == ApplicationStatus.WITHDRAWN

    def test_submitted_to_rejected(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        service.update_status(app_id, ApplicationStatus.READY)
        service.update_status(app_id, ApplicationStatus.QUEUED)
        service.update_status(app_id, ApplicationStatus.SUBMITTED)
        result = service.update_status(app_id, ApplicationStatus.REJECTED)
        assert result.current_status == ApplicationStatus.REJECTED

    def test_submitted_to_withdrawn(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        service.update_status(app_id, ApplicationStatus.READY)
        service.update_status(app_id, ApplicationStatus.QUEUED)
        service.update_status(app_id, ApplicationStatus.SUBMITTED)
        result = service.update_status(app_id, ApplicationStatus.WITHDRAWN)
        assert result.current_status == ApplicationStatus.WITHDRAWN

    def test_hired_to_archived(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        service.update_status(app_id, ApplicationStatus.READY)
        service.update_status(app_id, ApplicationStatus.QUEUED)
        service.update_status(app_id, ApplicationStatus.SUBMITTED)
        service.update_status(app_id, ApplicationStatus.INTERVIEW)
        service.update_status(app_id, ApplicationStatus.OFFER)
        service.update_status(app_id, ApplicationStatus.HIRED)
        result = service.archive(app_id)
        assert result.archived is True

    def test_offer_to_rejected(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        service.update_status(app_id, ApplicationStatus.READY)
        service.update_status(app_id, ApplicationStatus.QUEUED)
        service.update_status(app_id, ApplicationStatus.SUBMITTED)
        service.update_status(app_id, ApplicationStatus.INTERVIEW)
        service.update_status(app_id, ApplicationStatus.OFFER)
        result = service.update_status(app_id, ApplicationStatus.REJECTED)
        assert result.current_status == ApplicationStatus.REJECTED

    def test_archived_status_prevents_updates(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        service.archive(app_id)
        with pytest.raises(InvalidStatusTransitionError):
            service.update_status(app_id, ApplicationStatus.READY)

    def test_deleted_record_not_returned_by_get(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        service.delete(app_id)
        record = service.get(app_id)
        assert record is not None
        assert record.deleted is True

    def test_timeline_event_default_values(self):
        event = TimelineEvent(event_type="status_changed")
        assert event.actor == "system"
        assert event.reason is None

    def test_application_record_default_values(self):
        record = ApplicationRecord(application_id="test")
        assert record.priority == 0
        assert record.source_provider is None
        assert record.archived is False
        assert record.deleted is False

    def test_repeated_archive_raises(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        service.archive(app_id)
        with pytest.raises(InvalidArchiveStateError):
            service.archive(app_id)

    def test_repeated_restore_raises(self):
        service = ApplicationTrackingService()
        app_id = str(uuid.uuid4())
        service.create(app_id)
        with pytest.raises(InvalidArchiveStateError):
            service.restore(app_id)
