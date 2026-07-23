from __future__ import annotations

import contextlib
from threading import Lock
from typing import Any

from app.browser.config import BrowserConfig
from app.browser.context import ContextManager
from app.browser.schemas import SessionInfo, SessionState
from app.browser.validator import BrowserValidator


class SessionManager:
    def __init__(
        self,
        context_manager: ContextManager,
        config: BrowserConfig,
        validator: BrowserValidator,
    ) -> None:
        self._context_manager = context_manager
        self._config = config
        self._validator = validator
        self._lock = Lock()
        self._sessions: dict[str, dict[str, Any]] = {}

    def create_session(
        self,
        browser_id: str,
        context_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> SessionInfo:
        ctx_info = self._context_manager.get_context_info(browser_id, context_id)
        self._validator.validate_context_open(ctx_info)

        info = SessionInfo(
            browser_id=browser_id,
            context_id=context_id,
            state=SessionState.CREATED,
            metadata=metadata or {},
        )
        ctx_instance = self._context_manager.get_instance(browser_id, context_id)
        if ctx_instance is not None:
            page = ctx_instance.new_page()
            self._context_manager.add_page(browser_id, context_id, info.id, page)

        with self._lock:
            self._sessions[info.id] = {
                "info": info,
                "page": None,
            }
        return info

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._sessions.get(session_id)

    def get_session_info(self, session_id: str) -> SessionInfo | None:
        entry = self.get_session(session_id)
        if entry is None:
            return None
        return entry["info"]

    def get_page(self, session_id: str) -> Any:
        entry = self.get_session(session_id)
        if entry is None:
            page = self._context_manager.get_page("", "")
            return page
        page = entry.get("page")
        if page is not None:
            return page
        info = entry["info"]
        return self._context_manager.get_page(info.browser_id, info.context_id, session_id)

    def update_state(self, session_id: str, state: SessionState) -> None:
        with self._lock:
            entry = self._sessions.get(session_id)
            if entry is not None:
                entry["info"].state = state

    def close_session(self, session_id: str) -> None:
        with self._lock:
            entry = self._sessions.pop(session_id, None)
        if entry is not None:
            info = entry["info"]
            page = entry.get("page")
            if page is not None:
                with contextlib.suppress(Exception):
                    page.close()
            self._context_manager.remove_page(info.browser_id, info.context_id, session_id)
            info.state = SessionState.CLOSED

    def list_sessions(self) -> list[SessionInfo]:
        with self._lock:
            return [entry["info"] for entry in self._sessions.values()]

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)
