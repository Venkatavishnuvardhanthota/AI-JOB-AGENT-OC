from __future__ import annotations

import uuid

import pytest

from app.workflow.cache import WorkflowCache
from app.workflow.config import WorkflowConfig
from app.workflow.exceptions import (
    InvalidTransitionError,
    MaxRetriesExceededError,
    WorkflowLockedError,
)
from app.workflow.history import WorkflowHistory
from app.workflow.schemas import (
    HistoryEntry,
    TransitionType,
    WorkflowState,
    WorkflowStatus,
)
from app.workflow.service import WorkflowService
from app.workflow.state_machine import StateMachine
from app.workflow.transitions import TransitionManager
from app.workflow.validator import WorkflowValidator


class TestWorkflowState:
    def test_enum_values(self):
        assert WorkflowState.DISCOVERED.value == "discovered"
        assert WorkflowState.MATCHED.value == "matched"
        assert WorkflowState.PACKAGE_GENERATED.value == "package_generated"
        assert WorkflowState.READY_FOR_REVIEW.value == "ready_for_review"
        assert WorkflowState.APPROVED.value == "approved"
        assert WorkflowState.QUEUED.value == "queued"
        assert WorkflowState.SUBMITTED.value == "submitted"
        assert WorkflowState.TRACKING.value == "tracking"
        assert WorkflowState.INTERVIEW.value == "interview"
        assert WorkflowState.OFFER.value == "offer"
        assert WorkflowState.REJECTED.value == "rejected"

    def test_all_states_unique(self):
        values = [s.value for s in WorkflowState]
        assert len(values) == len(set(values))


class TestWorkflowValidator:
    def test_get_allowed_from_discovered(self):
        allowed = WorkflowValidator.get_allowed_transitions(WorkflowState.DISCOVERED)
        assert allowed == [WorkflowState.MATCHED]

    def test_get_allowed_from_matched(self):
        allowed = WorkflowValidator.get_allowed_transitions(WorkflowState.MATCHED)
        assert allowed == [WorkflowState.PACKAGE_GENERATED]

    def test_get_allowed_from_ready_for_review(self):
        allowed = WorkflowValidator.get_allowed_transitions(
            WorkflowState.READY_FOR_REVIEW
        )
        assert WorkflowState.APPROVED in allowed
        assert WorkflowState.REJECTED in allowed
        assert len(allowed) == 2

    def test_get_allowed_from_tracking(self):
        allowed = WorkflowValidator.get_allowed_transitions(WorkflowState.TRACKING)
        assert WorkflowState.INTERVIEW in allowed
        assert WorkflowState.REJECTED in allowed

    def test_get_allowed_from_interview(self):
        allowed = WorkflowValidator.get_allowed_transitions(WorkflowState.INTERVIEW)
        assert WorkflowState.OFFER in allowed
        assert WorkflowState.REJECTED in allowed

    def test_get_allowed_from_offer(self):
        allowed = WorkflowValidator.get_allowed_transitions(WorkflowState.OFFER)
        assert allowed == [WorkflowState.REJECTED]

    def test_get_allowed_from_rejected(self):
        allowed = WorkflowValidator.get_allowed_transitions(WorkflowState.REJECTED)
        assert allowed == []

    def test_valid_transition(self):
        validator = WorkflowValidator()
        status = WorkflowStatus(workflow_id="test")
        validator.validate_transition(status, WorkflowState.MATCHED)

    def test_valid_transition_same_state(self):
        validator = WorkflowValidator()
        status = WorkflowStatus(
            workflow_id="test", current_state=WorkflowState.SUBMITTED
        )
        validator.validate_transition(status, WorkflowState.SUBMITTED)

    def test_invalid_transition_submitted_to_matched(self):
        validator = WorkflowValidator()
        status = WorkflowStatus(
            workflow_id="test", current_state=WorkflowState.SUBMITTED
        )
        with pytest.raises(InvalidTransitionError):
            validator.validate_transition(status, WorkflowState.MATCHED)

    def test_invalid_transition_offer_to_queued(self):
        validator = WorkflowValidator()
        status = WorkflowStatus(
            workflow_id="test", current_state=WorkflowState.OFFER
        )
        with pytest.raises(InvalidTransitionError):
            validator.validate_transition(status, WorkflowState.QUEUED)

    def test_invalid_transition_rejected_to_submitted(self):
        validator = WorkflowValidator()
        status = WorkflowStatus(
            workflow_id="test", current_state=WorkflowState.REJECTED
        )
        with pytest.raises(InvalidTransitionError):
            validator.validate_transition(status, WorkflowState.SUBMITTED)

    def test_validate_retry_under_limit(self):
        validator = WorkflowValidator(max_retries=3)
        status = WorkflowStatus(workflow_id="test", retry_count=2)
        validator.validate_retry(status)

    def test_validate_retry_at_limit(self):
        validator = WorkflowValidator(max_retries=3)
        status = WorkflowStatus(workflow_id="test", retry_count=3)
        with pytest.raises(MaxRetriesExceededError):
            validator.validate_retry(status)

    def test_validate_retry_over_limit(self):
        validator = WorkflowValidator(max_retries=3)
        status = WorkflowStatus(workflow_id="test", retry_count=5)
        with pytest.raises(MaxRetriesExceededError):
            validator.validate_retry(status)

    def test_validate_rollback_with_previous(self):
        validator = WorkflowValidator()
        status = WorkflowStatus(
            workflow_id="test",
            current_state=WorkflowState.APPROVED,
            previous_state=WorkflowState.READY_FOR_REVIEW,
        )
        validator.validate_rollback(status)

    def test_validate_rollback_no_previous(self):
        validator = WorkflowValidator()
        status = WorkflowStatus(workflow_id="test", current_state=WorkflowState.DISCOVERED)
        with pytest.raises(InvalidTransitionError):
            validator.validate_rollback(status)

    def test_validate_rollback_not_strict(self):
        validator = WorkflowValidator(strict=False)
        status = WorkflowStatus(workflow_id="test", previous_state=None)
        validator.validate_rollback(status)


class TestStateMachine:
    def test_transition_forward(self):
        sm = StateMachine()
        status = WorkflowStatus(workflow_id="test")
        result = sm.transition(status, WorkflowState.MATCHED)
        assert result.current_state == WorkflowState.MATCHED
        assert result.previous_state == WorkflowState.DISCOVERED
        assert result.retry_count == 0

    def test_transition_same_state_increments_retry(self):
        sm = StateMachine()
        status = WorkflowStatus(
            workflow_id="test", current_state=WorkflowState.MATCHED
        )
        result = sm.transition(status, WorkflowState.MATCHED)
        assert result.current_state == WorkflowState.MATCHED
        assert result.retry_count == 1

    def test_transition_through_full_flow(self):
        sm = StateMachine()
        states = [
            WorkflowState.DISCOVERED,
            WorkflowState.MATCHED,
            WorkflowState.PACKAGE_GENERATED,
            WorkflowState.READY_FOR_REVIEW,
            WorkflowState.APPROVED,
            WorkflowState.QUEUED,
            WorkflowState.SUBMITTED,
            WorkflowState.TRACKING,
            WorkflowState.INTERVIEW,
            WorkflowState.OFFER,
        ]
        status = WorkflowStatus(workflow_id="test")
        for target in states[1:]:
            status = sm.transition(status, target)
            assert status.current_state == target

    def test_rollback_restores_previous(self):
        sm = StateMachine()
        status = WorkflowStatus(workflow_id="test")
        status = sm.transition(status, WorkflowState.MATCHED)
        result = sm.rollback(status)
        assert result.current_state == WorkflowState.DISCOVERED
        assert result.previous_state is None

    def test_rollback_no_previous(self):
        sm = StateMachine()
        status = WorkflowStatus(workflow_id="test", current_state=WorkflowState.DISCOVERED)
        with pytest.raises(InvalidTransitionError):
            sm.rollback(status)

    def test_can_transition_valid(self):
        sm = StateMachine()
        status = WorkflowStatus(workflow_id="test")
        assert sm.can_transition(status, WorkflowState.MATCHED) is True

    def test_can_transition_invalid(self):
        sm = StateMachine()
        status = WorkflowStatus(workflow_id="test")
        assert sm.can_transition(status, WorkflowState.SUBMITTED) is False

    def test_is_terminal_rejected(self):
        sm = StateMachine()
        assert sm.is_terminal(WorkflowState.REJECTED) is True

    def test_is_terminal_not_rejected(self):
        sm = StateMachine()
        assert sm.is_terminal(WorkflowState.DISCOVERED) is False
        assert sm.is_terminal(WorkflowState.OFFER) is False

    def testget_allowed_transitions(self):
        sm = StateMachine()
        allowed = sm.get_allowed_transitions(WorkflowState.DISCOVERED)
        assert allowed == [WorkflowState.MATCHED]


class TestTransitionManager:
    def test_apply_transition(self):
        sm = StateMachine()
        history = WorkflowHistory()
        tm = TransitionManager(sm, history)
        status = WorkflowStatus(workflow_id="test")
        result = tm.apply(status, WorkflowState.MATCHED)
        assert result.current_state == WorkflowState.MATCHED

    def test_apply_retry(self):
        sm = StateMachine()
        history = WorkflowHistory()
        tm = TransitionManager(sm, history)
        status = WorkflowStatus(
            workflow_id="test", current_state=WorkflowState.MATCHED
        )
        result = tm.apply(status, WorkflowState.MATCHED)
        assert result.retry_count == 1

    def test_apply_retry_exceeds_limit(self):
        sm = StateMachine()
        history = WorkflowHistory()
        config = WorkflowConfig(max_retries=2)
        tm = TransitionManager(sm, history, config)
        status = WorkflowStatus(
            workflow_id="test",
            current_state=WorkflowState.MATCHED,
            retry_count=2,
        )
        with pytest.raises(MaxRetriesExceededError):
            tm.apply(status, WorkflowState.MATCHED)

    def test_apply_locked_workflow(self):
        sm = StateMachine()
        history = WorkflowHistory()
        tm = TransitionManager(sm, history)
        status = WorkflowStatus(
            workflow_id="test", current_state=WorkflowState.DISCOVERED, locked=True
        )
        with pytest.raises(WorkflowLockedError):
            tm.apply(status, WorkflowState.MATCHED)

    def test_rollback(self):
        sm = StateMachine()
        history = WorkflowHistory()
        tm = TransitionManager(sm, history)
        status = WorkflowStatus(workflow_id="test")
        status = tm.apply(status, WorkflowState.MATCHED)
        result = tm.rollback(status)
        assert result.current_state == WorkflowState.DISCOVERED

    def test_rollback_locked(self):
        sm = StateMachine()
        history = WorkflowHistory()
        tm = TransitionManager(sm, history)
        status = WorkflowStatus(
            workflow_id="test",
            current_state=WorkflowState.MATCHED,
            previous_state=WorkflowState.DISCOVERED,
            locked=True,
        )
        with pytest.raises(WorkflowLockedError):
            tm.rollback(status)

    def test_lock_and_unlock(self):
        sm = StateMachine()
        history = WorkflowHistory()
        tm = TransitionManager(sm, history)
        status = WorkflowStatus(workflow_id="test")

        locked = tm.lock(status)
        assert locked.locked is True

        unlocked = tm.unlock(locked)
        assert unlocked.locked is False


class TestWorkflowHistory:
    def test_add_and_get_history(self):
        history = WorkflowHistory()
        entry = HistoryEntry(
            from_state=WorkflowState.DISCOVERED,
            to_state=WorkflowState.MATCHED,
        )
        history.add("wf-1", entry)
        entries = history.get_history("wf-1")
        assert len(entries) == 1
        assert entries[0].from_state == WorkflowState.DISCOVERED
        assert entries[0].to_state == WorkflowState.MATCHED

    def test_get_history_empty(self):
        history = WorkflowHistory()
        entries = history.get_history("nonexistent")
        assert entries == []

    def test_get_latest(self):
        history = WorkflowHistory()
        e1 = HistoryEntry(
            from_state=WorkflowState.DISCOVERED,
            to_state=WorkflowState.MATCHED,
        )
        e2 = HistoryEntry(
            from_state=WorkflowState.MATCHED,
            to_state=WorkflowState.PACKAGE_GENERATED,
        )
        history.add("wf-1", e1)
        history.add("wf-1", e2)
        latest = history.get_latest("wf-1")
        assert latest is not None
        assert latest.to_state == WorkflowState.PACKAGE_GENERATED

    def test_get_latest_empty(self):
        history = WorkflowHistory()
        assert history.get_latest("nonexistent") is None

    def test_count(self):
        history = WorkflowHistory()
        history.add(
            "wf-1",
            HistoryEntry(
                from_state=WorkflowState.DISCOVERED,
                to_state=WorkflowState.MATCHED,
            ),
        )
        history.add(
            "wf-1",
            HistoryEntry(
                from_state=WorkflowState.MATCHED,
                to_state=WorkflowState.PACKAGE_GENERATED,
            ),
        )
        assert history.count("wf-1") == 2
        assert history.count("nonexistent") == 0

    def test_clear_specific(self):
        history = WorkflowHistory()
        history.add(
            "wf-1",
            HistoryEntry(
                from_state=WorkflowState.DISCOVERED,
                to_state=WorkflowState.MATCHED,
            ),
        )
        history.add(
            "wf-2",
            HistoryEntry(
                from_state=WorkflowState.DISCOVERED,
                to_state=WorkflowState.MATCHED,
            ),
        )
        history.clear("wf-1")
        assert history.count("wf-1") == 0
        assert history.count("wf-2") == 1

    def test_clear_all(self):
        history = WorkflowHistory()
        history.add(
            "wf-1",
            HistoryEntry(
                from_state=WorkflowState.DISCOVERED,
                to_state=WorkflowState.MATCHED,
            ),
        )
        history.add(
            "wf-2",
            HistoryEntry(
                from_state=WorkflowState.DISCOVERED,
                to_state=WorkflowState.MATCHED,
            ),
        )
        history.clear()
        assert history.count("wf-1") == 0
        assert history.count("wf-2") == 0


class TestWorkflowCache:
    def test_set_and_get(self):
        config = WorkflowConfig(cache_ttl_seconds=300)
        cache = WorkflowCache(config)
        status = WorkflowStatus(workflow_id="test")
        cache.set("key1", status)
        result = cache.get("key1")
        assert result is not None
        assert result.workflow_id == "test"

    def test_get_missing(self):
        config = WorkflowConfig()
        cache = WorkflowCache(config)
        assert cache.get("nonexistent") is None

    def test_invalidate(self):
        config = WorkflowConfig()
        cache = WorkflowCache(config)
        status = WorkflowStatus(workflow_id="test")
        cache.set("key1", status)
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_clear(self):
        config = WorkflowConfig()
        cache = WorkflowCache(config)
        cache.set("k1", WorkflowStatus(workflow_id="t1"))
        cache.set("k2", WorkflowStatus(workflow_id="t2"))
        cache.clear()
        assert cache.get("k1") is None
        assert cache.get("k2") is None

    def test_ttl_expiry(self):
        config = WorkflowConfig(cache_ttl_seconds=0)
        cache = WorkflowCache(config)
        status = WorkflowStatus(workflow_id="test")
        cache.set("key1", status)
        import time
        time.sleep(0.01)
        result = cache.get("key1")
        assert result is None

    def test_thread_safety(self):
        config = WorkflowConfig()
        cache = WorkflowCache(config)
        import threading
        errors = []

        def worker(ident: str):
            try:
                for i in range(100):
                    key = f"{ident}-{i}"
                    cache.set(key, WorkflowStatus(workflow_id=key))
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


class TestWorkflowService:
    def test_create_workflow(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        status = service.create_workflow(wf_id)
        assert status.workflow_id == wf_id
        assert status.current_state == WorkflowState.DISCOVERED

    def test_create_workflow_with_metadata(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        status = service.create_workflow(wf_id, metadata={"job_id": "123"})
        assert status.metadata == {"job_id": "123"}

    def test_get_status_existing(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        service.create_workflow(wf_id)
        status = service.get_status(wf_id)
        assert status is not None
        assert status.workflow_id == wf_id

    def test_get_status_nonexistent(self):
        service = WorkflowService()
        assert service.get_status("nonexistent") is None

    def test_transition_creates_workflow_if_not_exists(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        result = service.transition(wf_id, WorkflowState.MATCHED)
        assert result.current_state == WorkflowState.MATCHED

    def test_transition_full_flow(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        expected = [
            WorkflowState.MATCHED,
            WorkflowState.PACKAGE_GENERATED,
            WorkflowState.READY_FOR_REVIEW,
            WorkflowState.APPROVED,
            WorkflowState.QUEUED,
            WorkflowState.SUBMITTED,
            WorkflowState.TRACKING,
            WorkflowState.INTERVIEW,
            WorkflowState.OFFER,
        ]
        status = None
        for state in expected:
            status = service.transition(wf_id, state)
            assert status.current_state == state
        assert status is not None

    def test_transition_to_rejected(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        service.transition(wf_id, WorkflowState.MATCHED)
        service.transition(wf_id, WorkflowState.PACKAGE_GENERATED)
        result = service.transition(wf_id, WorkflowState.READY_FOR_REVIEW)
        result = service.transition(wf_id, WorkflowState.REJECTED)
        assert result.current_state == WorkflowState.REJECTED
        assert service.is_terminal(wf_id) is True

    def test_invalid_transition_rejected_to_anything(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        service.transition(wf_id, WorkflowState.MATCHED)
        service.transition(wf_id, WorkflowState.PACKAGE_GENERATED)
        service.transition(wf_id, WorkflowState.READY_FOR_REVIEW)
        service.transition(wf_id, WorkflowState.REJECTED)
        with pytest.raises(InvalidTransitionError):
            service.transition(wf_id, WorkflowState.SUBMITTED)

    def test_can_transition_no_workflow(self):
        service = WorkflowService()
        assert service.can_transition("nonexistent", WorkflowState.MATCHED) is True

    def test_can_transition_existing(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        service.create_workflow(wf_id)
        assert service.can_transition(wf_id, WorkflowState.MATCHED) is True
        assert service.can_transition(wf_id, WorkflowState.SUBMITTED) is False

    def test_is_terminal_nonexistent(self):
        service = WorkflowService()
        assert service.is_terminal("nonexistent") is False

    def test_is_terminal_active(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        service.create_workflow(wf_id)
        assert service.is_terminal(wf_id) is False

    def test_get_history(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        service.transition(wf_id, WorkflowState.MATCHED, actor="user")
        history = service.get_history(wf_id)
        assert len(history) >= 1
        assert history[0].actor == "user"
        assert history[0].to_state == WorkflowState.MATCHED

    def test_get_history_nonexistent(self):
        service = WorkflowService()
        assert service.get_history("nonexistent") == []

    def test_lock_and_unlock_workflow(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        locked = service.lock_workflow(wf_id)
        assert locked.locked is True

        unlocked = service.unlock_workflow(wf_id)
        assert unlocked.locked is False

    def test_locked_prevents_transition(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        service.lock_workflow(wf_id)
        with pytest.raises(WorkflowLockedError):
            service.transition(wf_id, WorkflowState.MATCHED)

    def test_rollback(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        service.transition(wf_id, WorkflowState.MATCHED)
        service.transition(wf_id, WorkflowState.PACKAGE_GENERATED)
        result = service.rollback(wf_id)
        assert result.current_state == WorkflowState.MATCHED

    def test_rollback_nonexistent_creates(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        result = service.rollback(wf_id)
        assert result.current_state == WorkflowState.DISCOVERED

    def test_caching(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        s1 = service.create_workflow(wf_id)
        s2 = service.get_status(wf_id)
        assert s2 is not None
        assert s1.current_state == s2.current_state

    def test_invalidate_cache(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        service.create_workflow(wf_id)
        service.invalidate_cache(wf_id)
        assert service.get_status(wf_id) is None

    def test_clear_cache(self):
        service = WorkflowService()
        wf_id1 = str(uuid.uuid4())
        wf_id2 = str(uuid.uuid4())
        service.create_workflow(wf_id1)
        service.create_workflow(wf_id2)
        service.clear_cache()
        assert service.get_status(wf_id1) is None
        assert service.get_status(wf_id2) is None

    def test_deterministic_transitions(self):
        service = WorkflowService()
        wf_id1 = str(uuid.uuid4())
        wf_id2 = str(uuid.uuid4())
        service.transition(wf_id1, WorkflowState.MATCHED)
        service.transition(wf_id1, WorkflowState.PACKAGE_GENERATED)
        service.transition(wf_id2, WorkflowState.MATCHED)
        service.transition(wf_id2, WorkflowState.PACKAGE_GENERATED)
        s1 = service.get_status(wf_id1)
        s2 = service.get_status(wf_id2)
        assert s1 is not None and s2 is not None
        assert s1.current_state == s2.current_state

    def test_transition_with_reason(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        service.transition(wf_id, WorkflowState.MATCHED, reason="Skills match")
        history = service.get_history(wf_id)
        assert history[0].reason == "Skills match"

    def test_transition_with_custom_actor(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        service.transition(wf_id, WorkflowState.MATCHED, actor="user123")
        history = service.get_history(wf_id)
        assert history[0].actor == "user123"

    def test_rollback_with_reason(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        service.transition(wf_id, WorkflowState.MATCHED)
        service.rollback(wf_id, reason="Incorrect match")
        history = service.get_history(wf_id)
        rollback_entries = [
            e for e in history if e.transition_type == TransitionType.ROLLBACK
        ]
        assert len(rollback_entries) == 1
        assert rollback_entries[0].reason == "Incorrect match"

    def test_retry_idempotent(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        service.transition(wf_id, WorkflowState.MATCHED)
        s1 = service.transition(wf_id, WorkflowState.MATCHED)
        assert s1.retry_count == 1
        assert s1.current_state == WorkflowState.MATCHED

    def test_state_machine_property(self):
        service = WorkflowService()
        assert isinstance(service.state_machine, StateMachine)


class TestWorkflowConfig:
    def test_default_config(self):
        config = WorkflowConfig()
        assert config.cache_ttl_seconds == 300
        assert config.strict_validation is True
        assert config.max_retries == 3
        assert config.allow_rollback is True
        assert config.track_history is True

    def test_custom_config(self):
        config = WorkflowConfig(
            cache_ttl_seconds=600,
            strict_validation=False,
            max_retries=5,
            allow_rollback=False,
            track_history=False,
        )
        assert config.cache_ttl_seconds == 600
        assert config.strict_validation is False
        assert config.max_retries == 5
        assert config.allow_rollback is False
        assert config.track_history is False


class TestEdgeCases:
    def test_empty_history_no_error(self):
        service = WorkflowService()
        assert service.get_history("nonexistent") == []

    def test_transition_from_rejected_always_fails(self):
        service = WorkflowService()
        wf_id = str(uuid.uuid4())
        service.transition(wf_id, WorkflowState.MATCHED)
        service.transition(wf_id, WorkflowState.PACKAGE_GENERATED)
        service.transition(wf_id, WorkflowState.READY_FOR_REVIEW)
        service.transition(wf_id, WorkflowState.REJECTED)
        for state in WorkflowState:
            if state == WorkflowState.REJECTED:
                continue
            with pytest.raises(InvalidTransitionError):
                service.transition(wf_id, state)

    def test_workflow_status_serialization(self):
        status = WorkflowStatus(
            workflow_id="test",
            current_state=WorkflowState.MATCHED,
            previous_state=WorkflowState.DISCOVERED,
        )
        data = status.model_dump()
        assert data["workflow_id"] == "test"
        assert data["current_state"] == "matched"
        assert data["previous_state"] == "discovered"

    def test_history_entry_serialization(self):
        entry = HistoryEntry(
            from_state=WorkflowState.DISCOVERED,
            to_state=WorkflowState.MATCHED,
            actor="system",
            transition_type=TransitionType.TRANSITION,
        )
        data = entry.model_dump()
        assert data["from_state"] == "discovered"
        assert data["to_state"] == "matched"
        assert data["actor"] == "system"
        assert data["transition_type"] == "transition"
        assert data["success"] is True

    def test_history_entry_default_actor(self):
        entry = HistoryEntry(
            from_state=WorkflowState.DISCOVERED,
            to_state=WorkflowState.MATCHED,
        )
        assert entry.actor == "system"
        assert entry.transition_type == TransitionType.TRANSITION
