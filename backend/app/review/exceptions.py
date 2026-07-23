from __future__ import annotations

from app.core.exceptions import AppError


class ReviewError(AppError):
    status_code = 500
    code = "REVIEW_ERROR"
    message = "An error occurred in the review engine."


class ReviewNotFoundError(ReviewError):
    status_code = 404
    code = "REVIEW_NOT_FOUND"
    message = "Review record not found."


class DuplicateReviewError(ReviewError):
    status_code = 409
    code = "DUPLICATE_REVIEW"
    message = "A review already exists for this package."


class InvalidReviewStateError(ReviewError):
    status_code = 400
    code = "INVALID_REVIEW_STATE"
    message = "The requested action is not allowed in the current review state."


class InvalidReviewerError(ReviewError):
    status_code = 400
    code = "INVALID_REVIEWER"
    message = "The specified reviewer is not valid."


class ExpiredReviewError(ReviewError):
    status_code = 400
    code = "EXPIRED_REVIEW"
    message = "The review has expired and cannot be acted upon."


class OverrideNotAllowedError(ReviewError):
    status_code = 400
    code = "OVERRIDE_NOT_ALLOWED"
    message = "Override is not allowed for this review."


class AutoApprovalFailedError(ReviewError):
    status_code = 400
    code = "AUTO_APPROVAL_FAILED"
    message = "Auto-approval criteria were not met."


class ReviewCacheError(ReviewError):
    status_code = 500
    code = "REVIEW_CACHE_ERROR"
    message = "Cache operation failed."
