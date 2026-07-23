from __future__ import annotations

import os

from app.browser.exceptions import (
    BrowserNotLaunchedError,
    ContextClosedError,
    FileNotFoundError,
    FileSizeExceededError,
    InvalidFileExtensionError,
    InvalidSelectorError,
    MaxContextsExceededError,
    MaxPagesExceededError,
    SessionClosedError,
)
from app.browser.schemas import BrowserInfo, BrowserState, ContextInfo, ContextState, SessionInfo, SessionState


class BrowserValidator:
    def __init__(
        self,
        max_contexts: int = 5,
        max_pages: int = 10,
        max_upload_size_mb: int = 10,
        allowed_extensions: tuple[str, ...] = (".pdf", ".doc", ".docx", ".txt", ".rtf"),
    ) -> None:
        self._max_contexts = max_contexts
        self._max_pages = max_pages
        self._max_upload_size_bytes = max_upload_size_mb * 1024 * 1024
        self._allowed_extensions = allowed_extensions

    def validate_browser_launched(self, browser_info: BrowserInfo | None) -> BrowserInfo:
        if browser_info is None:
            raise BrowserNotLaunchedError(message="Browser instance not found.")
        if browser_info.state != BrowserState.OPEN:
            raise BrowserNotLaunchedError(message=f"Browser is in state '{browser_info.state.value}', expected 'open'.")
        return browser_info

    def validate_context_open(self, context_info: ContextInfo | None) -> ContextInfo:
        if context_info is None:
            raise ContextClosedError(message="Browser context not found.")
        if context_info.state != ContextState.OPEN:
            raise ContextClosedError(message="Browser context is closed.")
        return context_info

    def validate_session_open(self, session_info: SessionInfo | None) -> SessionInfo:
        if session_info is None:
            raise SessionClosedError(message="Session not found.")
        if session_info.state == SessionState.CLOSED:
            raise SessionClosedError(message="Session is closed.")
        return session_info

    def validate_selector(self, selector: str | None) -> str:
        if not selector:
            raise InvalidSelectorError(message="Selector cannot be empty.")
        return selector

    def validate_upload_file(self, file_path: str) -> str:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(message=f"File not found: '{file_path}'.")
        file_size = os.path.getsize(file_path)
        if file_size > self._max_upload_size_bytes:
            raise FileSizeExceededError(
                message=f"File size {file_size} bytes exceeds max {self._max_upload_size_bytes} bytes."
            )
        ext = os.path.splitext(file_path)[1].lower()
        if ext and self._allowed_extensions and ext not in self._allowed_extensions:
            raise InvalidFileExtensionError(
                message=f"File extension '{ext}' is not allowed. Allowed: {self._allowed_extensions}"
            )
        return file_path

    def validate_max_contexts(self, current_count: int) -> None:
        if current_count >= self._max_contexts:
            raise MaxContextsExceededError(message=f"Maximum contexts ({self._max_contexts}) reached.")

    def validate_max_pages(self, current_count: int) -> None:
        if current_count >= self._max_pages:
            raise MaxPagesExceededError(message=f"Maximum pages ({self._max_pages}) per context reached.")
