from __future__ import annotations

from datetime import datetime
from typing import Any

from app.application_tracking.config import ApplicationTrackingConfig
from app.application_tracking.metrics import MetricsCalculator
from app.application_tracking.schemas import (
    ApplicationRecord,
    ApplicationStatus,
    TimelineEvent,
    TimelineEventType,
)
from app.application_tracking.status import StatusManager
from app.application_tracking.timeline import TimelineManager
from app.application_tracking.validator import ApplicationTrackingValidator
from app.workflow.schemas import WorkflowState


class ApplicationTracker:
    def __init__(
        self,
        config: ApplicationTrackingConfig | None = None,
    ) -> None:
        self._config = config or ApplicationTrackingConfig()
        self._validator = ApplicationTrackingValidator(
            strict=self._config.strict_validation
        )
        self._timeline = TimelineManager()
        self._status = StatusManager(
            self._validator, self._timeline, self._config
        )
        self._metrics = MetricsCalculator()

    def create(
        self,
        application_id: str,
        existing: ApplicationRecord | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ApplicationRecord:
        self._validator.validate_create(application_id, existing)

        record = ApplicationRecord(
            application_id=application_id,
            metadata=metadata or {},
        )

        if self._config.track_timeline:
            self._timeline.add_event(
                record,
                event_type=TimelineEventType.APPLICATION_CREATED,
                metadata={"application_id": application_id},
            )

        if self._config.auto_calculate_metrics:
            self._metrics.refresh(record)

        return record

    def update_status(
        self,
        record: ApplicationRecord,
        new_status: ApplicationStatus,
        actor: str = "system",
        reason: str | None = None,
    ) -> ApplicationRecord:
        return self._status.update_status(record, new_status, actor, reason)

    def record_workflow_event(
        self,
        record: ApplicationRecord,
        workflow_state: WorkflowState,
        actor: str = "system",
        reason: str | None = None,
    ) -> ApplicationRecord:
        if self._config.track_timeline:
            self._timeline.add_workflow_event(record, workflow_state, actor, reason)
        record.workflow_state = workflow_state
        record.updated_at = datetime.utcnow()
        return record

    def add_event(
        self,
        record: ApplicationRecord,
        event_type: TimelineEventType | str,
        actor: str = "system",
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TimelineEvent:
        return self._timeline.add_event(
            record, event_type, actor, reason, metadata
        )

    def get_timeline(
        self,
        record: ApplicationRecord,
        reverse: bool = False,
    ) -> list[TimelineEvent]:
        return self._timeline.get_timeline(record, reverse)

    def get_metrics(
        self,
        record: ApplicationRecord,
    ) -> ApplicationRecord:
        self._metrics.refresh(record)
        return record

    def archive(
        self,
        record: ApplicationRecord,
        actor: str = "system",
        reason: str | None = None,
    ) -> ApplicationRecord:
        self._validator.validate_archive(record)
        record.archived = True
        record.archived_at = datetime.utcnow()
        record.updated_at = datetime.utcnow()

        if self._config.track_timeline:
            self._timeline.add_event(
                record,
                event_type=TimelineEventType.ARCHIVED,
                actor=actor,
                reason=reason,
            )

        return record

    def restore(
        self,
        record: ApplicationRecord,
        actor: str = "system",
        reason: str | None = None,
    ) -> ApplicationRecord:
        self._validator.validate_restore(record)
        record.archived = False
        record.archived_at = None
        record.updated_at = datetime.utcnow()

        if self._config.track_timeline:
            self._timeline.add_event(
                record,
                event_type=TimelineEventType.RESTORED,
                actor=actor,
                reason=reason,
            )

        return record

    def delete(
        self,
        record: ApplicationRecord,
    ) -> None:
        self._validator.validate_delete(record)
        record.deleted = True
        record.updated_at = datetime.utcnow()

    def validate_history(
        self,
        record: ApplicationRecord,
    ) -> None:
        self._validator.validate_history(record)
