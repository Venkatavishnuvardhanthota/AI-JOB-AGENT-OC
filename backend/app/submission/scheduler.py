from __future__ import annotations

from datetime import datetime, timedelta

from app.submission.schemas import SubmissionRecord, SubmissionState


class Scheduler:
    def schedule(
        self,
        record: SubmissionRecord,
        delay_seconds: float = 0.0,
    ) -> SubmissionRecord:
        if delay_seconds > 0:
            record.scheduled_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
            record.state = SubmissionState.SCHEDULED
        else:
            record.scheduled_at = datetime.utcnow()
            record.state = SubmissionState.SCHEDULED
        record.updated_at = datetime.utcnow()
        return record

    def is_due(self, record: SubmissionRecord) -> bool:
        if record.scheduled_at is None:
            return True
        return datetime.utcnow() >= record.scheduled_at

    def reschedule(
        self,
        record: SubmissionRecord,
        delay_seconds: float,
    ) -> SubmissionRecord:
        record.scheduled_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        record.state = SubmissionState.SCHEDULED
        record.updated_at = datetime.utcnow()
        return record

    def cancel_schedule(self, record: SubmissionRecord) -> SubmissionRecord:
        record.scheduled_at = None
        record.updated_at = datetime.utcnow()
        return record
