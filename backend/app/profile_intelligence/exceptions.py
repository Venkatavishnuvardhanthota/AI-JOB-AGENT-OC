from __future__ import annotations

from app.core.exceptions import AppError


class ProfileIntelligenceError(AppError):
    status_code = 500
    code = "PROFILE_INTELLIGENCE_ERROR"
    message = "A profile intelligence operation failed."


class ProfileExtractionError(ProfileIntelligenceError):
    code = "PROFILE_EXTRACTION_ERROR"
    message = "Failed to extract profile data."


class ProfileCacheError(ProfileIntelligenceError):
    code = "PROFILE_CACHE_ERROR"
    message = "Failed to cache profile intelligence."
