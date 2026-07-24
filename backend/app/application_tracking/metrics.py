from __future__ import annotations

from datetime import datetime

from app.application_tracking.schemas import ApplicationMetrics, ApplicationRecord


class MetricsCalculator:
    def calculate(
        self,
        record: ApplicationRecord,
    ) -> ApplicationMetrics:
        metrics = record.metrics.model_copy()
        now = datetime.utcnow()

        if record.submission_timestamp:
            delta = now - record.submission_timestamp
            metrics.days_since_submission = delta.days

        if record.timeline:
            first = record.timeline[0].timestamp
            delta = now - first
            metrics.total_lifecycle_duration_hours = round(delta.total_seconds() / 3600, 2)
            metrics.timeline_event_count = len(record.timeline)

        metrics.time_in_current_status_hours = self._calculate_time_in_status(record, now)

        return metrics

    def refresh(
        self,
        record: ApplicationRecord,
    ) -> None:
        record.metrics = self.calculate(record)

    @staticmethod
    def _calculate_time_in_status(
        record: ApplicationRecord,
        now: datetime,
    ) -> float:
        if not record.timeline:
            return 0.0

        relevant_events = [
            e
            for e in reversed(record.timeline)
            if e.metadata.get("new_status") == record.current_status.value
            or e.metadata.get("previous_status") == record.current_status.value
        ]

        if not relevant_events:
            first_event = record.timeline[0]
            delta = now - first_event.timestamp
            return round(delta.total_seconds() / 3600, 2)

        last_change = relevant_events[0].timestamp
        delta = now - last_change
        return round(delta.total_seconds() / 3600, 2)
