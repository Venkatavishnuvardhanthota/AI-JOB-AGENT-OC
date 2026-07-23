from __future__ import annotations

from app.core.exceptions import AppError


class ATSError(AppError):
    status_code = 502
    code = "ATS_ERROR"
    message = "An ATS operation failed."


class ATSProviderNotFoundError(ATSError):
    status_code = 404
    code = "ATS_PROVIDER_NOT_FOUND"
    message = "No ATS provider found for the given URL or name."


class ATSProviderUnavailableError(ATSError):
    code = "ATS_PROVIDER_UNAVAILABLE"
    message = "An ATS provider is not available."


class ATSNotSupportedError(ATSError):
    status_code = 400
    code = "ATS_NOT_SUPPORTED"
    message = "The given URL is not supported by any ATS provider."


class ATSLoginError(ATSError):
    status_code = 401
    code = "ATS_LOGIN_ERROR"
    message = "Failed to log in to the ATS provider."


class ATSNavigationError(ATSError):
    status_code = 400
    code = "ATS_NAVIGATION_ERROR"
    message = "Failed to navigate within the ATS provider."


class ATSJobNotFoundError(ATSError):
    status_code = 404
    code = "ATS_JOB_NOT_FOUND"
    message = "Job not found on the ATS provider."


class ATSApplicationError(ATSError):
    status_code = 400
    code = "ATS_APPLICATION_ERROR"
    message = "Failed to open or submit an application on the ATS provider."


class ATSValidationError(ATSError):
    status_code = 400
    code = "ATS_VALIDATION_ERROR"
    message = "ATS validation failed."


class ATSDetectionError(ATSError):
    status_code = 400
    code = "ATS_DETECTION_ERROR"
    message = "Failed to detect the ATS provider from the URL."


class ATSConfigError(ATSError):
    status_code = 500
    code = "ATS_CONFIG_ERROR"
    message = "ATS configuration error."


class ATSProviderError(ATSError):
    status_code = 502
    code = "ATS_PROVIDER_ERROR"
    message = "An ATS provider operation failed."


class ATSProviderTimeoutError(ATSProviderError):
    code = "ATS_PROVIDER_TIMEOUT"
    message = "ATS provider operation timed out."


class ATSProviderAuthError(ATSProviderError):
    status_code = 401
    code = "ATS_PROVIDER_AUTH_ERROR"
    message = "Authentication with the ATS provider failed."


class ATSProviderRateLimitError(ATSProviderError):
    status_code = 429
    code = "ATS_PROVIDER_RATE_LIMIT"
    message = "Rate limited by the ATS provider."


class ATSProviderStateError(ATSProviderError):
    code = "ATS_PROVIDER_STATE_ERROR"
    message = "The ATS provider is in an invalid state for the requested operation."


class ATSProviderRegistrationError(ATSProviderError):
    status_code = 500
    code = "ATS_PROVIDER_REGISTRATION_ERROR"
    message = "Failed to register the ATS provider."


class ATSProviderDuplicateError(ATSProviderError):
    status_code = 409
    code = "ATS_PROVIDER_DUPLICATE"
    message = "An ATS provider with the same name is already registered."
