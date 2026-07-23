from __future__ import annotations

from app.core.exceptions import AppError


class WorkflowError(AppError):
    status_code = 500
    code = "WORKFLOW_ERROR"
    message = "An error occurred in the workflow engine."


class InvalidTransitionError(WorkflowError):
    status_code = 400
    code = "INVALID_TRANSITION"
    message = "The requested transition is not allowed from the current state."


class WorkflowLockedError(WorkflowError):
    status_code = 409
    code = "WORKFLOW_LOCKED"
    message = "The workflow is currently locked and cannot process transitions."


class MaxRetriesExceededError(WorkflowError):
    status_code = 400
    code = "MAX_RETRIES_EXCEEDED"
    message = "Maximum retry attempts exceeded for this transition."


class WorkflowCacheError(WorkflowError):
    status_code = 500
    code = "WORKFLOW_CACHE_ERROR"
    message = "Cache operation failed."
