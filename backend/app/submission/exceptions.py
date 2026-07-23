from __future__ import annotations

from app.core.exceptions import AppError


class SubmissionError(AppError):
    status_code = 500
    code = "SUBMISSION_ERROR"
    message = "An error occurred in the submission engine."


class SubmissionNotFoundError(SubmissionError):
    status_code = 404
    code = "SUBMISSION_NOT_FOUND"
    message = "Submission record not found."


class DuplicateSubmissionError(SubmissionError):
    status_code = 409
    code = "DUPLICATE_SUBMISSION"
    message = "A submission already exists for this package."


class InvalidSubmissionStateError(SubmissionError):
    status_code = 400
    code = "INVALID_SUBMISSION_STATE"
    message = "The requested action is not allowed in the current submission state."


class SubmissionValidationError(SubmissionError):
    status_code = 400
    code = "SUBMISSION_VALIDATION_ERROR"
    message = "Submission validation failed."


class SubmissionNotReadyError(SubmissionError):
    status_code = 400
    code = "SUBMISSION_NOT_READY"
    message = "The application is not ready for submission."


class RetryExhaustedError(SubmissionError):
    status_code = 400
    code = "RETRY_EXHAUSTED"
    message = "Maximum retry attempts exhausted."


class NonRetryableFailureError(SubmissionError):
    status_code = 400
    code = "NON_RETRYABLE_FAILURE"
    message = "The failure is non-retryable."


class SubmissionCacheError(SubmissionError):
    status_code = 500
    code = "SUBMISSION_CACHE_ERROR"
    message = "Cache operation failed."
