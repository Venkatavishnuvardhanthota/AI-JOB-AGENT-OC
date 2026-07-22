from app.core.exceptions import AppError


class CoverLetterError(AppError):
    status_code = 500
    code = "COVER_LETTER_ERROR"
    message = "An error occurred during cover letter generation."


class CoverLetterGenerationError(CoverLetterError):
    status_code = 500
    code = "COVER_LETTER_GENERATION_ERROR"
    message = "Failed to generate cover letter."


class CoverLetterValidationError(CoverLetterError):
    status_code = 400
    code = "COVER_LETTER_VALIDATION_ERROR"
    message = "Invalid input for cover letter generation."


class CoverLetterCacheError(CoverLetterError):
    status_code = 500
    code = "COVER_LETTER_CACHE_ERROR"
    message = "Cache operation failed during cover letter generation."
