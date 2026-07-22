from __future__ import annotations

from app.core.exceptions import AppError


class JobDiscoveryError(AppError):
    status_code = 502
    code = "JOB_DISCOVERY_ERROR"
    message = "A job discovery operation failed."


class ProviderUnavailableError(JobDiscoveryError):
    code = "PROVIDER_UNAVAILABLE"
    message = "A job provider is not available."


class ProviderNotFoundError(JobDiscoveryError):
    status_code = 404
    code = "PROVIDER_NOT_FOUND"
    message = "No job provider found with the given name."


class SearchValidationError(JobDiscoveryError):
    status_code = 400
    code = "SEARCH_VALIDATION_ERROR"
    message = "Invalid job search parameters."


class NormalizationError(JobDiscoveryError):
    code = "NORMALIZATION_ERROR"
    message = "Failed to normalize job data from provider."


class DuplicateDetectionError(JobDiscoveryError):
    code = "DUPLICATE_DETECTION_ERROR"
    message = "Duplicate detection failed."
