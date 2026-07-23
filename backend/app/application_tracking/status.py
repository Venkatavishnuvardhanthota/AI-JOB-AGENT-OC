from __future__ import annotations

from datetime import datetime

from app.application_tracking.config import ApplicationTrackingConfig
from app.application_tracking.schemas import (
    ApplicationRecord,
    ApplicationStatus,
)
from app.application_tracking.timeline import TimelineManager
from app.application_tracking.validator import ApplicationTrackingValidator


class StatusManager:
    def __init__(
        self,
        validator: ApplicationTrackingValidator,
        timeline: TimelineManager,
        config: ApplicationTrackingConfig | None = None,
    ) -> None:
        self._validator = validator
        self._timeline = timeline
        self._config = config or ApplicationTrackingConfig()

    def update_status(
        self,
        record: ApplicationRecord,
        new_status: ApplicationStatus,
        actor: str = "system",
        reason: str | None = None,
    ) -> ApplicationRecord:
        if record.current_status == new_status:
            return record

        self._validator.validate_status_update(record, new_status)

        old_status = record.current_status
        record.current_status = new_status
        record.updated_at = datetime.utcnow()

        if new_status == ApplicationStatus.SUBMITTED and record.submission_timestamp is None:
            record.submission_timestamp = datetime.utcnow()

        if self._config.track_timeline:
            self._timeline.add_status_event(record, new_status, actor, reason)

        if self._config.auto_calculate_metrics:
            self._update_counts(record, old_status, new_status)

        return record

    @staticmethod
    def _update_counts(
        record: ApplicationRecord,
        old_status: ApplicationStatus,
        new_status: ApplicationStatus,
    ) -> None:
        record.metrics.status_change_count += 1

        interview_statuses = {ApplicationStatus.INTERVIEW}
        offer_statuses = {ApplicationStatus.OFFER}
        rejection_statuses = {ApplicationStatus.REJECTED}
        withdrawal_statuses = {ApplicationStatus.WITHDRAWN}

        if new_status in interview_statuses and old_status not in interview_statuses:
            record.metrics.number_of_interviews += 1
        if new_status in offer_statuses:
            record.metrics.offer_count += 1
        if new_status in rejection_statuses:
            record.metrics.rejection_count += 1
        if new_status in withdrawal_statuses:
            record.metrics.withdrawal_count += 1
