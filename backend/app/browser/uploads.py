from __future__ import annotations

from typing import Any

from app.browser.exceptions import ElementNotFoundError, UploadError
from app.browser.validator import BrowserValidator


class UploadManager:
    def __init__(self, validator: BrowserValidator) -> None:
        self._validator = validator

    def upload_file(
        self,
        page: Any,
        selector: str,
        file_path: str,
        timeout_ms: float = 30000.0,
    ) -> None:
        validated_path = self._validator.validate_upload_file(file_path)
        try:
            element = page.locator(selector)
            if not element.is_visible():
                raise ElementNotFoundError(message=f"Upload element '{selector}' is not visible.")
            element.set_input_files(validated_path, timeout=timeout_ms)
        except ElementNotFoundError:
            raise
        except Exception as e:
            raise UploadError(message=f"Failed to upload file '{file_path}' to '{selector}': {e!s}") from e

    def upload_multiple(
        self,
        page: Any,
        selector: str,
        file_paths: list[str],
        timeout_ms: float = 30000.0,
    ) -> None:
        validated_paths = [self._validator.validate_upload_file(p) for p in file_paths]
        try:
            element = page.locator(selector)
            if not element.is_visible():
                raise ElementNotFoundError(message=f"Upload element '{selector}' is not visible.")
            element.set_input_files(validated_paths, timeout=timeout_ms)
        except ElementNotFoundError:
            raise
        except Exception as e:
            raise UploadError(message=f"Failed to upload files to '{selector}': {e!s}") from e
