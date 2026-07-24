from __future__ import annotations

from datetime import datetime

import structlog

from app.submission_engine.schemas import SubmissionState, SubmissionStatus

logger = structlog.get_logger(__name__)


class SubmissionStateMachine:
    def __init__(self) -> None:
        self._logger = logger.bind(service="submission_state")
        self._transitions: dict[SubmissionState, list[SubmissionState]] = {
            SubmissionState.PENDING: [SubmissionState.VALIDATING, SubmissionState.CANCELLED],
            SubmissionState.VALIDATING: [SubmissionState.VALIDATED, SubmissionState.FAILED, SubmissionState.CANCELLED],
            SubmissionState.VALIDATED: [SubmissionState.EXECUTING_FIELDS, SubmissionState.CANCELLED],
            SubmissionState.EXECUTING_FIELDS: [
                SubmissionState.EXECUTING_UPLOADS,
                SubmissionState.FAILED,
                SubmissionState.BLOCKED,
                SubmissionState.CANCELLED,
            ],
            SubmissionState.EXECUTING_UPLOADS: [
                SubmissionState.AWAITING_CONFIRMATION,
                SubmissionState.FAILED,
                SubmissionState.BLOCKED,
                SubmissionState.CANCELLED,
            ],
            SubmissionState.AWAITING_CONFIRMATION: [SubmissionState.SUBMITTING, SubmissionState.CANCELLED],
            SubmissionState.SUBMITTING: [SubmissionState.CONFIRMING, SubmissionState.FAILED, SubmissionState.BLOCKED],
            SubmissionState.CONFIRMING: [SubmissionState.COMPLETED, SubmissionState.FAILED],
            SubmissionState.COMPLETED: [],
            SubmissionState.FAILED: [SubmissionState.PENDING],
            SubmissionState.BLOCKED: [SubmissionState.PENDING],
            SubmissionState.CANCELLED: [],
        }

    def can_transition(self, current: SubmissionState, target: SubmissionState) -> bool:
        allowed = self._transitions.get(current, [])
        return target in allowed

    def transition(self, status: SubmissionStatus, target: SubmissionState) -> SubmissionStatus:
        if not self.can_transition(status.state, target):
            raise ValueError(f"Cannot transition from {status.state.value} to {target.value}")

        status.state = target
        status.updated_at = datetime.utcnow()
        return status

    def get_allowed_transitions(self, state: SubmissionState) -> list[SubmissionState]:
        return list(self._transitions.get(state, []))

    def is_terminal(self, state: SubmissionState) -> bool:
        return state in (SubmissionState.COMPLETED, SubmissionState.CANCELLED)

    def is_failure(self, state: SubmissionState) -> bool:
        return state in (SubmissionState.FAILED, SubmissionState.BLOCKED)
