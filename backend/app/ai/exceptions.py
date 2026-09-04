from app.core.exceptions import AppError


class AIError(AppError):
    status_code = 502
    code = "AI_ERROR"
    message = "An AI operation failed."


class ProviderUnavailableError(AIError):
    code = "PROVIDER_UNAVAILABLE"
    message = "The AI provider is not available."


class ProviderDisabledError(AIError):
    status_code = 403
    code = "PROVIDER_DISABLED"
    message = "The AI provider is disabled."


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


class ConfigurationMissingError(AIError):
    status_code = 500
    code = "AI_CONFIGURATION_MISSING"
    message = "Required AI configuration is missing."


class InvalidAPIKeyError(AIError):
    status_code = 401
    code = "INVALID_API_KEY"
    message = "The API key for the AI provider is invalid or missing."


class AIServiceValidationError(AIError):
    status_code = 400
    code = "AI_VALIDATION_ERROR"
    message = "Invalid AI request parameters."


class RateLimitedError(AIError):
    status_code = 429
    code = "AI_RATE_LIMITED"
    message = "AI provider rate limit exceeded."


class InvalidResponseError(AIError):
    status_code = 502
    code = "INVALID_RESPONSE"
    message = "Received an invalid response from the AI provider."


class ProviderInitializationFailedError(AIError):
    status_code = 500
    code = "PROVIDER_INITIALIZATION_FAILED"
    message = "AI provider initialization failed."


class NetworkError(AIError):
    status_code = 502
    code = "NETWORK_ERROR"
    message = "Network error while communicating with the AI provider."


class PromptTemplateError(AIError):
    status_code = 400
    code = "PROMPT_TEMPLATE_ERROR"
    message = "Invalid prompt template."


class MissingVariableError(PromptTemplateError):
    code = "MISSING_VARIABLE"
    message = "Required template variables are missing."


class RenderError(PromptTemplateError):
    code = "RENDER_ERROR"
    message = "Failed to render prompt template."


class ResponseParsingError(AIError):
    status_code = 502
    code = "RESPONSE_PARSING_ERROR"
    message = "Failed to parse AI response."


class ResponseValidationError(AIError):
    status_code = 502
    code = "RESPONSE_VALIDATION_ERROR"
    message = "AI response failed validation."
