from __future__ import annotations

from app.core.exceptions import AppError


class SubmissionEngineError(AppError):
    status_code = 502
    code = "SUBMISSION_ENGINE_ERROR"
    message = "A submission engine operation failed."


class SubmissionValidationError(SubmissionEngineError):
    status_code = 400
    code = "SUBMISSION_VALIDATION_ERROR"
    message = "Submission validation failed."


class SubmissionExecutionError(SubmissionEngineError):
    code = "SUBMISSION_EXECUTION_ERROR"
    message = "Failed to execute a submission step."


class SubmissionConfirmationError(SubmissionEngineError):
    code = "SUBMISSION_CONFIRMATION_ERROR"
    message = "Failed to confirm submission."


class SubmissionRecoveryError(SubmissionEngineError):
    code = "SUBMISSION_RECOVERY_ERROR"
    message = "Failed to recover from a submission error."


class SubmissionSafetyError(SubmissionEngineError):
    status_code = 400
    code = "SUBMISSION_SAFETY_ERROR"
    message = "A safety check blocked the submission."


class SubmissionTimeoutError(SubmissionEngineError):
    code = "SUBMISSION_TIMEOUT_ERROR"
    message = "Submission timed out."


class SubmissionRejectedError(SubmissionEngineError):
    status_code = 400
    code = "SUBMISSION_REJECTED_ERROR"
    message = "Submission was rejected by the provider."


class SubmissionProviderNotFoundError(SubmissionEngineError):
    status_code = 404
    code = "SUBMISSION_PROVIDER_NOT_FOUND"
    message = "No submission provider found."


class SubmissionConfigError(SubmissionEngineError):
    status_code = 500
    code = "SUBMISSION_CONFIG_ERROR"
    message = "Submission configuration error."
