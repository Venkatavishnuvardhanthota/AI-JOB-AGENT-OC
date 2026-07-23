from __future__ import annotations

import contextlib
from datetime import datetime
from threading import Lock
from typing import Any

from app.browser.config import BrowserConfig
from app.browser.schemas import BrowserInfo, BrowserState, BrowserType


class BrowserManager:
    def __init__(self, config: BrowserConfig) -> None:
        self._config = config
        self._browsers: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def create_browser(
        self,
        browser_type: BrowserType = BrowserType.CHROMIUM,
        headless: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> BrowserInfo:
        info = BrowserInfo(
            browser_type=browser_type,
            headless=headless if headless is not None else self._config.headless,
            state=BrowserState.OPEN,
            launched_at=datetime.utcnow(),
            metadata=metadata or {},
        )
        with self._lock:
            self._browsers[info.id] = {
                "info": info,
                "instance": None,
                "contexts": {},
            }
        return info

    def get_browser(self, browser_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._browsers.get(browser_id)

    def get_browser_info(self, browser_id: str) -> BrowserInfo | None:
        entry = self.get_browser(browser_id)
        if entry is None:
            return None
        return entry["info"]

    def update_browser_info(self, browser_id: str, info: BrowserInfo) -> None:
        with self._lock:
            entry = self._browsers.get(browser_id)
            if entry is not None:
                entry["info"] = info

    def attach_instance(self, browser_id: str, instance: Any) -> None:
        with self._lock:
            entry = self._browsers.get(browser_id)
            if entry is not None:
                entry["instance"] = instance

    def get_instance(self, browser_id: str) -> Any:
        with self._lock:
            entry = self._browsers.get(browser_id)
            if entry is None:
                return None
            return entry["instance"]

    def close_browser(self, browser_id: str) -> None:
        with self._lock:
            entry = self._browsers.pop(browser_id, None)
            if entry is not None:
                instance = entry.get("instance")
                if instance is not None:
                    with contextlib.suppress(Exception):
                        instance.close()

    def close_all(self) -> None:
        with self._lock:
            for entry in self._browsers.values():
                instance = entry.get("instance")
                if instance is not None:
                    with contextlib.suppress(Exception):
                        instance.close()
            self._browsers.clear()

    def list_browsers(self) -> list[BrowserInfo]:
        with self._lock:
            return [entry["info"] for entry in self._browsers.values()]

    def count(self) -> int:
        with self._lock:
            return len(self._browsers)

    def add_context(self, browser_id: str, context_id: str, context_data: dict[str, Any]) -> None:
        with self._lock:
            entry = self._browsers.get(browser_id)
            if entry is not None:
                entry["contexts"][context_id] = context_data
                info = entry["info"]
                info.context_count = len(entry["contexts"])

    def remove_context(self, browser_id: str, context_id: str) -> None:
        with self._lock:
            entry = self._browsers.get(browser_id)
            if entry is not None:
                entry["contexts"].pop(context_id, None)
                info = entry["info"]
                info.context_count = len(entry["contexts"])

    def get_context(self, browser_id: str, context_id: str) -> dict[str, Any] | None:
        with self._lock:
            entry = self._browsers.get(browser_id)
            if entry is None:
                return None
            return entry["contexts"].get(context_id)

    def context_count(self, browser_id: str) -> int:
        with self._lock:
            entry = self._browsers.get(browser_id)
            if entry is None:
                return 0
            return len(entry["contexts"])
