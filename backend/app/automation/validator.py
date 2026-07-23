from __future__ import annotations

from app.automation.exceptions import (
    DuplicateJobError,
    InvalidCronExpressionError,
    InvalidScheduleError,
    InvalidTriggerError,
    JobDisabledError,
    JobNotFoundError,
    JobPausedError,
    MissingTargetError,
    RetryLimitExceededError,
)
from app.automation.schemas import AutomationJob, AutomationTrigger, JobState, TriggerType
from app.automation.triggers import TriggerEvaluator


class AutomationValidator:
    def __init__(self, strict: bool = True) -> None:
        self._strict = strict
        self._trigger_evaluator = TriggerEvaluator()

    def validate_create(self, job: AutomationJob, existing: AutomationJob | None) -> None:
        if existing is not None:
            raise DuplicateJobError(
                message=f"Automation job '{job.id}' already exists."
            )
        self._validate_job_fields(job)

    def validate_update(self, job: AutomationJob, existing: AutomationJob | None) -> AutomationJob:
        if existing is None:
            raise JobNotFoundError(
                message=f"Automation job '{job.id}' not found."
            )
        self._validate_job_fields(job)
        return existing

    def validate_get(self, job: AutomationJob | None) -> AutomationJob:
        if job is None:
            raise JobNotFoundError(message="Automation job not found.")
        return job

    def validate_execution(self, job: AutomationJob) -> None:
        if not job.enabled:
            raise JobDisabledError(
                message=f"Automation job '{job.id}' is disabled."
            )
        if job.state == JobState.PAUSED:
            raise JobPausedError(
                message=f"Automation job '{job.id}' is paused."
            )
        if job.state in (JobState.COMPLETED, JobState.CANCELLED):
            raise JobDisabledError(
                message=f"Automation job '{job.id}' is in state '{job.state.value}'."
            )
        if not job.target_module or not job.target_action:
            raise MissingTargetError(
                message=f"Automation job '{job.id}' has no target module or action."
            )

    def validate_retry(self, job: AutomationJob) -> None:
        if job.retry_count >= job.policy.max_retries:
            raise RetryLimitExceededError(
                message=f"Automation job '{job.id}' has exhausted retries "
                f"({job.retry_count}/{job.policy.max_retries})."
            )

    def validate_cancel(self, job: AutomationJob) -> None:
        if job.state == JobState.CANCELLED:
            raise JobDisabledError(
                message=f"Automation job '{job.id}' is already cancelled."
            )

    def validate_trigger(self, trigger: AutomationTrigger) -> None:
        errors = self._trigger_evaluator.validate(trigger)
        if errors:
            if any("cron" in e.lower() for e in errors):
                raise InvalidCronExpressionError(
                    message="; ".join(errors)
                )
            raise InvalidTriggerError(
                message="; ".join(errors)
            )

    def validate_schedule(self, job: AutomationJob) -> None:
        if job.automation_type.value in ("one_time", "recurring") and job.trigger.trigger_type == TriggerType.MANUAL:
                raise InvalidScheduleError(
                    message=f"Automation type '{job.automation_type.value}' "
                    f"requires a non-manual trigger."
                )

    def _validate_job_fields(self, job: AutomationJob) -> None:
        if not job.target_module:
            raise MissingTargetError(
                message="Target module is required."
            )
        if not job.target_action:
            raise MissingTargetError(
                message="Target action is required."
            )
        if self._strict:
            trigger_errors = self._trigger_evaluator.validate(job.trigger)
            if trigger_errors:
                if any("cron" in e.lower() for e in trigger_errors):
                    raise InvalidCronExpressionError(
                        message="; ".join(trigger_errors)
                    )
                raise InvalidTriggerError(
                    message="; ".join(trigger_errors)
                )
