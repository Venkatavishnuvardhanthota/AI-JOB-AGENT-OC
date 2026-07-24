from __future__ import annotations

from typing import Any

from app.application_tracking.schemas import (
    ApplicationRecord,
    ApplicationStatus,
    TimelineEvent,
    TimelineEventType,
)
from app.workflow.schemas import WorkflowState


class TimelineManager:
    def add_event(
        self,
        record: ApplicationRecord,
        event_type: TimelineEventType | str,
        actor: str = "system",
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TimelineEvent:
        event = TimelineEvent(
            event_type=event_type,
            actor=actor,
            reason=reason,
            metadata=metadata or {},
        )
        record.timeline.append(event)
        return event

    def add_status_event(
        self,
        record: ApplicationRecord,
        status: ApplicationStatus,
        actor: str = "system",
        reason: str | None = None,
    ) -> TimelineEvent:
        event_type = self._status_to_event_type(status)
        return self.add_event(
            record,
            event_type=event_type,
            actor=actor,
            reason=reason,
            metadata={"new_status": status.value, "previous_status": record.current_status.value},
        )

    def add_workflow_event(
        self,
        record: ApplicationRecord,
        workflow_state: WorkflowState,
        actor: str = "system",
        reason: str | None = None,
    ) -> TimelineEvent:
        return self.add_event(
            record,
            event_type=TimelineEventType.WORKFLOW_EVENT,
            actor=actor,
            reason=reason,
            metadata={
                "workflow_state": workflow_state.value,
                "previous_workflow_state": record.workflow_state.value if record.workflow_state else None,
            },
        )

    def get_timeline(
        self,
        record: ApplicationRecord,
        reverse: bool = False,
    ) -> list[TimelineEvent]:
        events = list(record.timeline)
        if reverse:
            events.reverse()
        return events

    def get_events_by_type(
        self,
        record: ApplicationRecord,
        event_type: TimelineEventType | str,
    ) -> list[TimelineEvent]:
        return [e for e in record.timeline if e.event_type == event_type]

    @staticmethod
    def _status_to_event_type(status: ApplicationStatus) -> TimelineEventType:
        mapping: dict[ApplicationStatus, TimelineEventType] = {
            ApplicationStatus.DRAFT: TimelineEventType.APPLICATION_CREATED,
            ApplicationStatus.READY: TimelineEventType.STATUS_CHANGED,
            ApplicationStatus.QUEUED: TimelineEventType.QUEUED,
            ApplicationStatus.SUBMITTED: TimelineEventType.SUBMITTED,
            ApplicationStatus.VIEWED: TimelineEventType.VIEWED,
            ApplicationStatus.IN_REVIEW: TimelineEventType.STATUS_CHANGED,
            ApplicationStatus.ASSESSMENT: TimelineEventType.ASSESSMENT,
            ApplicationStatus.INTERVIEW: TimelineEventType.INTERVIEW_SCHEDULED,
            ApplicationStatus.OFFER: TimelineEventType.OFFER,
            ApplicationStatus.HIRED: TimelineEventType.STATUS_CHANGED,
            ApplicationStatus.REJECTED: TimelineEventType.REJECTED,
            ApplicationStatus.WITHDRAWN: TimelineEventType.WITHDRAWN,
            ApplicationStatus.ARCHIVED: TimelineEventType.ARCHIVED,
        }
        return mapping.get(status, TimelineEventType.STATUS_CHANGED)
