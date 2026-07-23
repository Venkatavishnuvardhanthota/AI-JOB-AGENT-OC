from __future__ import annotations

import contextlib
from typing import Any

from app.browser.config import BrowserConfig
from app.browser.manager import BrowserManager
from app.browser.schemas import ContextInfo, ContextState
from app.browser.validator import BrowserValidator


class ContextManager:
    def __init__(
        self,
        browser_manager: BrowserManager,
        config: BrowserConfig,
        validator: BrowserValidator,
    ) -> None:
        self._browser_manager = browser_manager
        self._config = config
        self._validator = validator

    def create_context(
        self,
        browser_id: str,
        storage_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ContextInfo:
        browser_info = self._browser_manager.get_browser_info(browser_id)
        self._validator.validate_browser_launched(browser_info)
        current_count = self._browser_manager.context_count(browser_id)
        self._validator.validate_max_contexts(current_count)

        info = ContextInfo(
            browser_id=browser_id,
            is_persistent=storage_state is not None,
            storage_state=storage_state or {},
            metadata=metadata or {},
        )
        self._browser_manager.add_context(
            browser_id,
            info.id,
            {
                "info": info,
                "instance": None,
                "pages": {},
            },
        )
        return info

    def get_context_info(self, browser_id: str, context_id: str) -> ContextInfo | None:
        ctx = self._browser_manager.get_context(browser_id, context_id)
        if ctx is None:
            return None
        return ctx["info"]

    def attach_instance(self, browser_id: str, context_id: str, instance: Any) -> None:
        ctx = self._browser_manager.get_context(browser_id, context_id)
        if ctx is not None:
            ctx["instance"] = instance

    def get_instance(self, browser_id: str, context_id: str) -> Any:
        ctx = self._browser_manager.get_context(browser_id, context_id)
        if ctx is None:
            return None
        return ctx.get("instance")

    def close_context(self, browser_id: str, context_id: str) -> None:
        ctx = self._browser_manager.get_context(browser_id, context_id)
        if ctx is not None:
            instance = ctx.get("instance")
            if instance is not None:
                with contextlib.suppress(Exception):
                    instance.close()
            info = ctx["info"]
            info.state = ContextState.CLOSED
            self._browser_manager.remove_context(browser_id, context_id)

    def add_page(self, browser_id: str, context_id: str, page_id: str, page_instance: Any) -> None:
        ctx = self._browser_manager.get_context(browser_id, context_id)
        if ctx is not None:
            self._validator.validate_max_pages(len(ctx["pages"]))
            ctx["pages"][page_id] = page_instance
            info = ctx["info"]
            info.page_count = len(ctx["pages"])

    def remove_page(self, browser_id: str, context_id: str, page_id: str) -> None:
        ctx = self._browser_manager.get_context(browser_id, context_id)
        if ctx is not None:
            ctx["pages"].pop(page_id, None)
            info = ctx["info"]
            info.page_count = len(ctx["pages"])

    def get_page(self, browser_id: str, context_id: str, page_id: str) -> Any:
        ctx = self._browser_manager.get_context(browser_id, context_id)
        if ctx is None:
            return None
        return ctx["pages"].get(page_id)

    def list_pages(self, browser_id: str, context_id: str) -> list[str]:
        ctx = self._browser_manager.get_context(browser_id, context_id)
        if ctx is None:
            return []
        return list(ctx["pages"].keys())
