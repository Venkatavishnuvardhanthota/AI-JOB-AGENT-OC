from app.core.exceptions import AppError


class JobMatchingError(AppError):
    status_code = 500
    code = "JOB_MATCHING_ERROR"
    message = "An error occurred during job matching."


class MatchValidationError(JobMatchingError):
    status_code = 400
    code = "MATCH_VALIDATION_ERROR"
    message = "Invalid input for job matching."


class MatchCacheError(JobMatchingError):
    status_code = 500
    code = "MATCH_CACHE_ERROR"
    message = "Cache operation failed."
