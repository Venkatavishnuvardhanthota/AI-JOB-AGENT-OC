from app.core.exceptions import AppError


class AIError(AppError):
    status_code = 502
    code = "AI_ERROR"
    message = "An AI operation failed."


class ProviderUnavailableError(AIError):
    code = "PROVIDER_UNAVAILABLE"
    message = "The AI provider is not available."


class ProviderNotFoundError(AIError):
    status_code = 404
    code = "PROVIDER_NOT_FOUND"
    message = "No AI provider found with the given name."


class ModelUnavailableError(AIError):
    code = "MODEL_UNAVAILABLE"
    message = "The requested model is not available on this provider."


class GenerationError(AIError):
    code = "GENERATION_ERROR"
    message = "AI content generation failed."


class TimeoutError(AIError):
    status_code = 504
    code = "AI_TIMEOUT"
    message = "The AI provider request timed out."


class ConfigurationError(AIError):
    status_code = 500
    code = "AI_CONFIGURATION_ERROR"
    message = "The AI subsystem is misconfigured."


class AIServiceValidationError(AIError):
    status_code = 400
    code = "AI_VALIDATION_ERROR"
    message = "Invalid AI request parameters."
