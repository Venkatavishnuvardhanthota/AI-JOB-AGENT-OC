from __future__ import annotations

from app.core.exceptions import AppError


class FormsError(AppError):
    status_code = 502
    code = "FORMS_ERROR"
    message = "A form intelligence operation failed."


class FormAnalysisError(FormsError):
    code = "FORM_ANALYSIS_ERROR"
    message = "Failed to analyze the form."


class FormClassificationError(FormsError):
    code = "FORM_CLASSIFICATION_ERROR"
    message = "Failed to classify a form field."


class FormMappingError(FormsError):
    code = "FORM_MAPPING_ERROR"
    message = "Failed to map a form field to application data."


class FormValidationError(FormsError):
    status_code = 400
    code = "FORM_VALIDATION_ERROR"
    message = "Form validation failed."


class FormPlanningError(FormsError):
    code = "FORM_PLANNING_ERROR"
    message = "Failed to generate an execution plan."


class FormProviderNotFoundError(FormsError):
    status_code = 404
    code = "FORM_PROVIDER_NOT_FOUND"
    message = "No form provider found."


class FormProviderError(FormsError):
    code = "FORM_PROVIDER_ERROR"
    message = "A form provider operation failed."


class FormConfigError(FormsError):
    status_code = 500
    code = "FORM_CONFIG_ERROR"
    message = "Form intelligence configuration error."
