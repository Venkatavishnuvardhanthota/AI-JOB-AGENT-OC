class AppError(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, details: dict | None = None):
        self.message = message or self.message
        self.details = details or {}


class ValidationError(AppError):
    status_code = 400
    code = "VALIDATION_ERROR"
    message = "Validation failed."


class AuthenticationError(AppError):
    status_code = 401
    code = "AUTHENTICATION_ERROR"
    message = "Authentication failed."


class AuthorizationError(AppError):
    status_code = 403
    code = "AUTHORIZATION_ERROR"
    message = "Insufficient permissions."


class NotFoundError(AppError):
    status_code = 404
    code = "RESOURCE_NOT_FOUND"
    message = "Resource not found."


class ConflictError(AppError):
    status_code = 409
    code = "DUPLICATE_RESOURCE"
    message = "Resource already exists."


class RateLimitError(AppError):
    status_code = 429
    code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests."


class ProviderError(AppError):
    status_code = 502
    code = "PROVIDER_ERROR"
    message = "External provider error."


class AIProviderError(ProviderError):
    code = "AI_PROVIDER_ERROR"
    message = "AI provider error."


class JobProviderError(ProviderError):
    code = "JOB_PROVIDER_ERROR"
    message = "Job provider error."


class BrowserAutomationError(ProviderError):
    code = "BROWSER_AUTOMATION_ERROR"
    message = "Browser automation error."


class DatabaseError(AppError):
    status_code = 500
    code = "DATABASE_ERROR"
    message = "Database operation failed."
