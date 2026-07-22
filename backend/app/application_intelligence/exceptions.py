from __future__ import annotations

from app.core.exceptions import AppError


class ApplicationIntelligenceError(AppError):
    status_code = 500
    code = "APPLICATION_INTELLIGENCE_ERROR"
    message = "An error occurred during application intelligence analysis."


class AnalysisValidationError(ApplicationIntelligenceError):
    status_code = 400
    code = "ANALYSIS_VALIDATION_ERROR"
    message = "Invalid input for application intelligence analysis."


class AnalysisCacheError(ApplicationIntelligenceError):
    status_code = 500
    code = "ANALYSIS_CACHE_ERROR"
    message = "Cache operation failed."
