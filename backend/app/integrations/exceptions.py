from __future__ import annotations

from app.core.exceptions import AppError


class IntegrationError(AppError):
    status_code = 502
    code = "INTEGRATION_ERROR"
    message = "An integration operation failed."


class ProviderNotFoundError(IntegrationError):
    status_code = 404
    code = "PROVIDER_NOT_FOUND"
    message = "No notification provider found with the given name."


class ProviderUnavailableError(IntegrationError):
    code = "PROVIDER_UNAVAILABLE"
    message = "The notification provider is not available."


class ProviderDuplicateError(IntegrationError):
    status_code = 409
    code = "PROVIDER_DUPLICATE"
    message = "A provider with the same name is already registered."


class DeliveryError(IntegrationError):
    code = "DELIVERY_ERROR"
    message = "Failed to deliver notification."


class ConfigurationError(IntegrationError):
    status_code = 500
    code = "INTEGRATION_CONFIG_ERROR"
    message = "Integration configuration error."


class CredentialValidationError(IntegrationError):
    status_code = 401
    code = "CREDENTIAL_VALIDATION_ERROR"
    message = "Provider credential validation failed."


class TemplateNotFoundError(IntegrationError):
    status_code = 404
    code = "TEMPLATE_NOT_FOUND"
    message = "Notification template not found."


class TemplateRenderError(IntegrationError):
    code = "TEMPLATE_RENDER_ERROR"
    message = "Failed to render notification template."


class RetryExhaustedError(IntegrationError):
    code = "RETRY_EXHAUSTED"
    message = "All retry attempts exhausted for notification delivery."


class DeadLetterError(IntegrationError):
    code = "DEAD_LETTER_ERROR"
    message = "Notification moved to dead letter queue."


class HMACSigningError(IntegrationError):
    code = "HMAC_SIGNING_ERROR"
    message = "Failed to sign webhook payload."
