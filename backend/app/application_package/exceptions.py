from __future__ import annotations

from app.core.exceptions import AppError


class ApplicationPackageError(AppError):
    status_code = 500
    code = "APPLICATION_PACKAGE_ERROR"
    message = "An error occurred during application package generation."


class PackageValidationError(ApplicationPackageError):
    status_code = 400
    code = "PACKAGE_VALIDATION_ERROR"
    message = "Invalid input for application package generation."


class PackageCacheError(ApplicationPackageError):
    status_code = 500
    code = "PACKAGE_CACHE_ERROR"
    message = "Cache operation failed."
