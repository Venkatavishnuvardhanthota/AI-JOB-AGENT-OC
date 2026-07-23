from __future__ import annotations

from app.core.exceptions import AppError


class ApplicationTrackingError(AppError):
    status_code = 500
    code = "APPLICATION_TRACKING_ERROR"
    message = "An error occurred in the application tracking system."


class ApplicationNotFoundError(ApplicationTrackingError):
    status_code = 404
    code = "APPLICATION_NOT_FOUND"
    message = "Application record not found."


class DuplicateApplicationError(ApplicationTrackingError):
    status_code = 409
    code = "DUPLICATE_APPLICATION"
    message = "An application with this ID already exists."


class InvalidStatusTransitionError(ApplicationTrackingError):
    status_code = 400
    code = "INVALID_STATUS_TRANSITION"
    message = "The requested status transition is not allowed."


class InvalidArchiveStateError(ApplicationTrackingError):
    status_code = 400
    code = "INVALID_ARCHIVE_STATE"
    message = "Application is already in the requested archive state."


class CorruptedHistoryError(ApplicationTrackingError):
    status_code = 500
    code = "CORRUPTED_HISTORY"
    message = "Application history data is corrupted."


class TrackingCacheError(ApplicationTrackingError):
    status_code = 500
    code = "TRACKING_CACHE_ERROR"
    message = "Cache operation failed."
