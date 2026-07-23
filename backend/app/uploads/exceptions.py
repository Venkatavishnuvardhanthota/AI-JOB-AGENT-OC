from __future__ import annotations

from app.core.exceptions import AppError


class UploadError(AppError):
    status_code = 502
    code = "UPLOAD_ERROR"
    message = "A document upload operation failed."


class UploadValidationError(UploadError):
    status_code = 400
    code = "UPLOAD_VALIDATION_ERROR"
    message = "Document validation failed."


class UploadExecutionError(UploadError):
    code = "UPLOAD_EXECUTION_ERROR"
    message = "Failed to execute document upload."


class UploadVerificationError(UploadError):
    code = "UPLOAD_VERIFICATION_ERROR"
    message = "Failed to verify document upload."


class UploadCapabilityError(UploadError):
    code = "UPLOAD_CAPABILITY_ERROR"
    message = "Provider does not support the requested upload capability."


class UploadTimeoutError(UploadError):
    code = "UPLOAD_TIMEOUT_ERROR"
    message = "Document upload timed out."


class UploadRejectedError(UploadError):
    status_code = 400
    code = "UPLOAD_REJECTED_ERROR"
    message = "Document upload was rejected by the provider."


class UploadProviderNotFoundError(UploadError):
    status_code = 404
    code = "UPLOAD_PROVIDER_NOT_FOUND"
    message = "No upload provider found."


class UploadConfigError(UploadError):
    status_code = 500
    code = "UPLOAD_CONFIG_ERROR"
    message = "Upload configuration error."
