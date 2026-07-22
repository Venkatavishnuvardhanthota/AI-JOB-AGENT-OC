from app.core.exceptions import AppError


class ResumeOptimizationError(AppError):
    status_code = 500
    code = "RESUME_OPTIMIZATION_ERROR"
    message = "An error occurred during resume optimization."


class ResumeOptimizationValidationError(ResumeOptimizationError):
    status_code = 400
    code = "RESUME_OPTIMIZATION_VALIDATION_ERROR"
    message = "Invalid input for resume optimization."


class ResumeOptimizationCacheError(ResumeOptimizationError):
    status_code = 500
    code = "RESUME_OPTIMIZATION_CACHE_ERROR"
    message = "Cache operation failed during resume optimization."
