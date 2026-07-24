from __future__ import annotations

from typing import Any

from app.application_tracking.cache import TrackingCache
from app.application_tracking.config import ApplicationTrackingConfig
from app.application_tracking.schemas import (
    ApplicationRecord,
    ApplicationStatus,
    TimelineEvent,
    TimelineEventType,
)
from app.application_tracking.tracker import ApplicationTracker
from app.workflow.schemas import WorkflowState


class ApplicationTrackingService:
    def __init__(
        self,
        config: ApplicationTrackingConfig | None = None,
    ) -> None:
        self._config = config or ApplicationTrackingConfig()
        self._tracker = ApplicationTracker(self._config)
        self._cache = TrackingCache(self._config)

    def create(
        self,
        application_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> ApplicationRecord:
        existing = self._cache.get(application_id)
        record = self._tracker.create(application_id, existing, metadata)
        self._cache.set(application_id, record)
        return record

    def update_status(
        self,
        application_id: str,
        new_status: ApplicationStatus,
        actor: str = "system",
        reason: str | None = None,
    ) -> ApplicationRecord:
        record = self._get_or_create(application_id)
        result = self._tracker.update_status(record, new_status, actor, reason)
        self._cache.set(application_id, result)
        return result

    def record_workflow_event(
        self,
        application_id: str,
        workflow_state: WorkflowState,
        actor: str = "system",
        reason: str | None = None,
    ) -> ApplicationRecord:
        record = self._get_or_create(application_id)
        result = self._tracker.record_workflow_event(record, workflow_state, actor, reason)
        self._cache.set(application_id, result)
        return result

    def add_event(
        self,
        application_id: str,
        event_type: TimelineEventType | str,
        actor: str = "system",
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TimelineEvent:
        record = self._get_or_create(application_id)
        event = self._tracker.add_event(record, event_type, actor, reason, metadata)
        self._cache.set(application_id, record)
        return event

    def get(self, application_id: str) -> ApplicationRecord | None:
        return self._cache.get(application_id)

    def get_history(
        self,
        application_id: str,
        reverse: bool = False,
    ) -> list[TimelineEvent]:
        record = self._cache.get(application_id)
        if record is None:
            return []
        return self._tracker.get_timeline(record, reverse)

    def get_metrics(
        self,
        application_id: str,
    ) -> ApplicationRecord | None:
        record = self._cache.get(application_id)
        if record is None:
            return None
        return self._tracker.get_metrics(record)

    def archive(
        self,
        application_id: str,
        actor: str = "system",
        reason: str | None = None,
    ) -> ApplicationRecord:
        record = self._get_or_create(application_id)
        result = self._tracker.archive(record, actor, reason)
        self._cache.set(application_id, result)
        return result

    def restore(
        self,
        application_id: str,
        actor: str = "system",
        reason: str | None = None,
    ) -> ApplicationRecord:
        record = self._get_or_create(application_id)
        result = self._tracker.restore(record, actor, reason)
        self._cache.set(application_id, result)
        return result

    def delete(self, application_id: str) -> None:
        record = self._cache.get(application_id)
        if record is not None:
            self._tracker.delete(record)
            self._cache.set(application_id, record)

    def invalidate_cache(self, application_id: str) -> None:
        self._cache.invalidate(application_id)

    def clear_cache(self) -> None:
        self._cache.clear()

    def _get_or_create(self, application_id: str) -> ApplicationRecord:
        record = self._cache.get(application_id)
        if record is None:
            record = self._tracker.create(application_id)
            self._cache.set(application_id, record)
        return record
