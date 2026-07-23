from __future__ import annotations

from app.core.exceptions import AppError


class BrowserError(AppError):
    status_code = 500
    code = "BROWSER_ERROR"
    message = "An error occurred in the browser automation framework."


class BrowserNotFoundError(BrowserError):
    status_code = 404
    code = "BROWSER_NOT_FOUND"
    message = "Browser instance not found."


class BrowserNotLaunchedError(BrowserError):
    status_code = 400
    code = "BROWSER_NOT_LAUNCHED"
    message = "Browser has not been launched."


class ContextNotFoundError(BrowserError):
    status_code = 404
    code = "CONTEXT_NOT_FOUND"
    message = "Browser context not found."


class ContextClosedError(BrowserError):
    status_code = 400
    code = "CONTEXT_CLOSED"
    message = "Browser context is closed."


class SessionNotFoundError(BrowserError):
    status_code = 404
    code = "SESSION_NOT_FOUND"
    message = "Session not found."


class SessionClosedError(BrowserError):
    status_code = 400
    code = "SESSION_CLOSED"
    message = "Session is closed."


class NavigationError(BrowserError):
    status_code = 400
    code = "NAVIGATION_ERROR"
    message = "Navigation failed."


class TimeoutError(BrowserError):
    status_code = 408
    code = "TIMEOUT_ERROR"
    message = "Operation timed out."


class ElementNotFoundError(BrowserError):
    status_code = 404
    code = "ELEMENT_NOT_FOUND"
    message = "Element not found on the page."


class InvalidSelectorError(BrowserError):
    status_code = 400
    code = "INVALID_SELECTOR"
    message = "The provided selector is invalid."


class UploadError(BrowserError):
    status_code = 400
    code = "UPLOAD_ERROR"
    message = "File upload failed."


class FileNotFoundError(BrowserError):
    status_code = 404
    code = "FILE_NOT_FOUND"
    message = "File not found for upload."


class FileSizeExceededError(BrowserError):
    status_code = 400
    code = "FILE_SIZE_EXCEEDED"
    message = "File size exceeds the maximum allowed."


class InvalidFileExtensionError(BrowserError):
    status_code = 400
    code = "INVALID_FILE_EXTENSION"
    message = "File extension is not allowed."


class DownloadError(BrowserError):
    status_code = 400
    code = "DOWNLOAD_ERROR"
    message = "File download failed."


class ScreenshotError(BrowserError):
    status_code = 500
    code = "SCREENSHOT_ERROR"
    message = "Screenshot capture failed."


class CookieError(BrowserError):
    status_code = 400
    code = "COOKIE_ERROR"
    message = "Cookie operation failed."


class StorageError(BrowserError):
    status_code = 500
    code = "STORAGE_ERROR"
    message = "Storage operation failed."


class BrowserCacheError(BrowserError):
    status_code = 500
    code = "BROWSER_CACHE_ERROR"
    message = "Cache operation failed."


class MaxContextsExceededError(BrowserError):
    status_code = 429
    code = "MAX_CONTEXTS_EXCEEDED"
    message = "Maximum number of browser contexts exceeded."


class MaxPagesExceededError(BrowserError):
    status_code = 429
    code = "MAX_PAGES_EXCEEDED"
    message = "Maximum number of pages per context exceeded."
