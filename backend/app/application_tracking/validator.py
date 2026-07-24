from __future__ import annotations

from app.application_tracking.exceptions import (
    ApplicationNotFoundError,
    CorruptedHistoryError,
    DuplicateApplicationError,
    InvalidArchiveStateError,
    InvalidStatusTransitionError,
)
from app.application_tracking.schemas import ApplicationRecord, ApplicationStatus


class ApplicationTrackingValidator:
    def __init__(self, strict: bool = True) -> None:
        self._strict = strict

    def validate_create(
        self,
        application_id: str,
        existing: ApplicationRecord | None,
    ) -> None:
        if existing is not None:
            raise DuplicateApplicationError(message=f"Application '{application_id}' already exists.")

    def validate_get(self, record: ApplicationRecord | None) -> ApplicationRecord:
        if record is None:
            raise ApplicationNotFoundError(message="Application record not found.")
        if record.deleted:
            raise ApplicationNotFoundError(message="Application record has been deleted.")
        return record

    def validate_status_update(
        self,
        record: ApplicationRecord,
        new_status: ApplicationStatus,
    ) -> None:
        if record.archived:
            raise InvalidStatusTransitionError(message="Cannot update status of an archived application.")
        allowed = self._get_allowed_statuses(record.current_status)
        if new_status not in allowed:
            raise InvalidStatusTransitionError(
                message=f"Cannot transition from {record.current_status.value} "
                f"to {new_status.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )

    def validate_archive(
        self,
        record: ApplicationRecord,
    ) -> None:
        if record.archived:
            raise InvalidArchiveStateError(message=f"Application '{record.application_id}' is already archived.")

    def validate_restore(
        self,
        record: ApplicationRecord,
    ) -> None:
        if not record.archived:
            raise InvalidArchiveStateError(message=f"Application '{record.application_id}' is not archived.")

    def validate_delete(self, record: ApplicationRecord | None) -> ApplicationRecord:
        if record is None:
            raise ApplicationNotFoundError(message="Application record not found.")
        return record

    def validate_history(
        self,
        record: ApplicationRecord,
    ) -> None:
        if not self._strict:
            return
        if record.timeline:
            timestamps = [e.timestamp for e in record.timeline]
            for i in range(1, len(timestamps)):
                if timestamps[i] < timestamps[i - 1]:
                    raise CorruptedHistoryError(message="Timeline events are not in chronological order.")

    @staticmethod
    def _get_allowed_statuses(
        current: ApplicationStatus,
    ) -> list[ApplicationStatus]:
        transitions: dict[ApplicationStatus, list[ApplicationStatus]] = {
            ApplicationStatus.DRAFT: [
                ApplicationStatus.READY,
                ApplicationStatus.WITHDRAWN,
                ApplicationStatus.ARCHIVED,
            ],
            ApplicationStatus.READY: [
                ApplicationStatus.QUEUED,
                ApplicationStatus.WITHDRAWN,
                ApplicationStatus.ARCHIVED,
            ],
            ApplicationStatus.QUEUED: [
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.WITHDRAWN,
                ApplicationStatus.ARCHIVED,
            ],
            ApplicationStatus.SUBMITTED: [
                ApplicationStatus.VIEWED,
                ApplicationStatus.IN_REVIEW,
                ApplicationStatus.ASSESSMENT,
                ApplicationStatus.INTERVIEW,
                ApplicationStatus.OFFER,
                ApplicationStatus.REJECTED,
                ApplicationStatus.WITHDRAWN,
                ApplicationStatus.ARCHIVED,
            ],
            ApplicationStatus.VIEWED: [
                ApplicationStatus.IN_REVIEW,
                ApplicationStatus.ASSESSMENT,
                ApplicationStatus.INTERVIEW,
                ApplicationStatus.OFFER,
                ApplicationStatus.REJECTED,
                ApplicationStatus.WITHDRAWN,
                ApplicationStatus.ARCHIVED,
            ],
            ApplicationStatus.IN_REVIEW: [
                ApplicationStatus.ASSESSMENT,
                ApplicationStatus.INTERVIEW,
                ApplicationStatus.OFFER,
                ApplicationStatus.REJECTED,
                ApplicationStatus.WITHDRAWN,
                ApplicationStatus.ARCHIVED,
            ],
            ApplicationStatus.ASSESSMENT: [
                ApplicationStatus.INTERVIEW,
                ApplicationStatus.OFFER,
                ApplicationStatus.REJECTED,
                ApplicationStatus.WITHDRAWN,
                ApplicationStatus.ARCHIVED,
            ],
            ApplicationStatus.INTERVIEW: [
                ApplicationStatus.OFFER,
                ApplicationStatus.REJECTED,
                ApplicationStatus.WITHDRAWN,
                ApplicationStatus.ARCHIVED,
            ],
            ApplicationStatus.OFFER: [
                ApplicationStatus.HIRED,
                ApplicationStatus.REJECTED,
                ApplicationStatus.WITHDRAWN,
                ApplicationStatus.ARCHIVED,
            ],
            ApplicationStatus.HIRED: [
                ApplicationStatus.ARCHIVED,
            ],
            ApplicationStatus.REJECTED: [
                ApplicationStatus.ARCHIVED,
            ],
            ApplicationStatus.WITHDRAWN: [
                ApplicationStatus.ARCHIVED,
            ],
            ApplicationStatus.ARCHIVED: [],
        }
        return transitions.get(current, [])
