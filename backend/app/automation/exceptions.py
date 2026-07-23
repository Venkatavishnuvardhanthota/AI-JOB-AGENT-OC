from __future__ import annotations

from app.core.exceptions import AppError


class AutomationError(AppError):
    status_code = 500
    code = "AUTOMATION_ERROR"
    message = "An error occurred in the automation engine."


class JobNotFoundError(AutomationError):
    status_code = 404
    code = "JOB_NOT_FOUND"
    message = "Automation job not found."


class DuplicateJobError(AutomationError):
    status_code = 409
    code = "DUPLICATE_JOB"
    message = "An automation job with this ID already exists."


class InvalidTriggerError(AutomationError):
    status_code = 400
    code = "INVALID_TRIGGER"
    message = "The trigger configuration is invalid."


class InvalidCronExpressionError(AutomationError):
    status_code = 400
    code = "INVALID_CRON_EXPRESSION"
    message = "The cron expression is invalid."


class JobDisabledError(AutomationError):
    status_code = 400
    code = "JOB_DISABLED"
    message = "The automation job is disabled."


class JobPausedError(AutomationError):
    status_code = 400
    code = "JOB_PAUSED"
    message = "The automation job is paused."


class MissingTargetError(AutomationError):
    status_code = 400
    code = "MISSING_TARGET"
    message = "The automation job has no target module or action."


class InvalidParameterError(AutomationError):
    status_code = 400
    code = "INVALID_PARAMETER"
    message = "The automation job parameters are invalid."


class InvalidScheduleError(AutomationError):
    status_code = 400
    code = "INVALID_SCHEDULE"
    message = "The schedule configuration is invalid."


class RetryLimitExceededError(AutomationError):
    status_code = 400
    code = "RETRY_LIMIT_EXCEEDED"
    message = "Maximum retry attempts exceeded for this job."


class AutomationCacheError(AutomationError):
    status_code = 500
    code = "AUTOMATION_CACHE_ERROR"
    message = "Cache operation failed."


class QueueFullError(AutomationError):
    status_code = 429
    code = "QUEUE_FULL"
    message = "The automation queue is full."


class JobAlreadyRunningError(AutomationError):
    status_code = 409
    code = "JOB_ALREADY_RUNNING"
    message = "The automation job is already running."
