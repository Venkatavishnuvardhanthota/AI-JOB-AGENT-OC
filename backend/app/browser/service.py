from __future__ import annotations

from typing import Any

from app.browser.cache import BrowserCache
from app.browser.config import BrowserConfig
from app.browser.context import ContextManager
from app.browser.cookies import CookieManager
from app.browser.downloads import DownloadManager
from app.browser.manager import BrowserManager
from app.browser.navigation import NavigationHelper
from app.browser.schemas import NavigationResult
from app.browser.screenshots import ScreenshotManager
from app.browser.selectors import SelectorHelper
from app.browser.session import SessionManager
from app.browser.storage import StorageManager
from app.browser.uploads import UploadManager
from app.browser.validator import BrowserValidator
from app.browser.waits import WaitStrategy


class BrowserService:
    def __init__(
        self,
        config: BrowserConfig | None = None,
        downloads_path: str = "downloads",
        screenshots_path: str = "screenshots",
    ) -> None:
        self.config = config or BrowserConfig()
        self.validator = BrowserValidator(
            max_contexts=self.config.max_contexts_per_browser,
            max_pages=self.config.max_pages_per_context,
            max_upload_size_mb=self.config.max_upload_size_mb,
            allowed_extensions=self.config.allowed_upload_extensions,
        )
        self.cache = BrowserCache(self.config)
        self.waits = WaitStrategy(self.config.wait_timeout_ms)
        self.navigation = NavigationHelper(self.waits)
        self.selectors = SelectorHelper()
        self.manager = BrowserManager(self.config)
        self.downloads = DownloadManager(downloads_path)
        self.screenshots = ScreenshotManager(
            screenshots_path,
            max_files=self.config.max_screenshot_files,
        )
        self.cookies = CookieManager()
        self.storage = StorageManager()
        self.uploads = UploadManager(self.validator)
        self.contexts = ContextManager(self.manager, self.config, self.validator)
        self.sessions = SessionManager(self.contexts, self.config, self.validator)

    def create_browser(
        self,
        browser_type: str = "chromium",
        headless: bool | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        info = self.manager.create_browser(browser_type, headless, metadata)
        return info.model_dump()

    def get_browser_info(self, browser_id: str) -> dict[str, Any] | None:
        info = self.manager.get_browser_info(browser_id)
        if info is None:
            return None
        return info.model_dump()

    def close_browser(self, browser_id: str) -> None:
        self.manager.close_browser(browser_id)

    def close_all(self) -> None:
        self.manager.close_all()

    def list_browsers(self) -> list[dict[str, Any]]:
        return [info.model_dump() for info in self.manager.list_browsers()]

    def create_context(
        self,
        browser_id: str,
        storage_state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        info = self.contexts.create_context(browser_id, storage_state, metadata)
        return info.model_dump()

    def create_session(
        self,
        browser_id: str,
        context_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        info = self.sessions.create_session(browser_id, context_id, metadata)
        return info.model_dump()

    def navigate(
        self,
        page: Any,
        url: str,
        timeout_ms: float = 60000.0,
        wait_until: str = "load",
    ) -> NavigationResult:
        return self.navigation.goto(page, url, timeout_ms, wait_until)

    def reload(self, page: Any, timeout_ms: float = 60000.0) -> NavigationResult:
        return self.navigation.reload(page, timeout_ms)

    def go_back(self, page: Any, timeout_ms: float = 60000.0) -> NavigationResult:
        return self.navigation.back(page, timeout_ms)

    def go_forward(self, page: Any, timeout_ms: float = 60000.0) -> NavigationResult:
        return self.navigation.forward(page, timeout_ms)

    def safe_click(self, page: Any, selector: str, timeout_ms: float | None = None) -> None:
        self.navigation.safe_click(page, selector, timeout_ms or self.config.default_timeout_ms)

    def safe_fill(self, page: Any, selector: str, value: str, timeout_ms: float | None = None) -> None:
        self.navigation.safe_fill(page, selector, value, timeout_ms or self.config.default_timeout_ms)

    def safe_select(self, page: Any, selector: str, value: str, timeout_ms: float | None = None) -> None:
        self.navigation.safe_select(page, selector, value, timeout_ms or self.config.default_timeout_ms)

    def wait_for_selector(self, page: Any, selector: str) -> Any:
        return self.waits.wait_for_selector(page, selector)

    def wait_for_network_idle(self, page: Any) -> None:
        self.waits.wait_for_network_idle(page)

    def wait_for_load_state(self, page: Any, state: str = "load") -> None:
        self.waits.wait_for_load_state(page, state)

    def wait_for_url(self, page: Any, url_pattern: str) -> None:
        self.waits.wait_for_url(page, url_pattern)

    def wait_for_timeout(self, page: Any, duration_ms: float) -> None:
        self.waits.wait_for_timeout(page, duration_ms)

    def click(self, page: Any, selector: str, timeout_ms: float = 10000.0) -> None:
        self.selectors.click(page, selector, timeout_ms)

    def fill(self, page: Any, selector: str, value: str, timeout_ms: float = 10000.0) -> None:
        self.selectors.fill(page, selector, value, timeout_ms)

    def select_option(self, page: Any, selector: str, value: str, timeout_ms: float = 10000.0) -> None:
        self.selectors.select_option(page, selector, value, timeout_ms)

    def get_text(self, page: Any, selector: str, timeout_ms: float = 10000.0) -> str:
        return self.selectors.get_text(page, selector, timeout_ms)

    def is_visible(self, page: Any, selector: str) -> bool:
        return self.selectors.is_visible(page, selector)

    def take_screenshot(
        self,
        page: Any,
        name: str | None = None,
        full_page: bool = False,
    ) -> str:
        from app.browser.schemas import ScreenshotOptions

        return self.screenshots.take_screenshot(
            page,
            name,
            ScreenshotOptions(full_page=full_page),
        )

    def take_failure_screenshot(
        self,
        page: Any,
        error_context: str = "failure",
    ) -> str:
        return self.screenshots.take_failure_screenshot(page, error_context)

    def capture_download(self, page: Any, timeout_ms: float = 60000.0) -> dict[str, Any]:
        info = self.downloads.capture_download(page, timeout_ms)
        return info.model_dump()

    def upload_file(
        self,
        page: Any,
        selector: str,
        file_path: str,
        timeout_ms: float = 30000.0,
    ) -> None:
        self.uploads.upload_file(page, selector, file_path, timeout_ms)

    def get_cookies(self, page: Any) -> list[dict[str, Any]]:
        return [c.model_dump() for c in self.cookies.get_cookies(page)]

    def set_cookies(self, page: Any, cookies: list[dict[str, Any]]) -> None:
        from app.browser.schemas import Cookie

        parsed = [Cookie(**c) for c in cookies]
        self.cookies.set_cookies(page, parsed)

    def clear_cookies(self, page: Any) -> None:
        self.cookies.clear_cookies(page)

    def get_storage_state(self, context: Any) -> dict[str, Any]:
        return self.storage.get_storage_state(context)

    def cache_get(self, key: str) -> Any:
        return self.cache.get(key)

    def cache_set(self, key: str, value: Any) -> None:
        self.cache.set(key, value)

    def cache_invalidate(self, key: str) -> None:
        self.cache.invalidate(key)

    def cache_clear(self) -> None:
        self.cache.clear()

    def query_selector(self, parent: Any, selector: str) -> Any:
        return parent.query_selector(selector)

    def query_selector_all(self, parent: Any, selector: str) -> list[Any]:
        return parent.query_selector_all(selector)

    def get_text_content(self, element: Any) -> str:
        return element.text_content() or ""

    def get_attribute(self, element: Any, attribute: str) -> str | None:
        return element.get_attribute(attribute)

    def get_content(self, page: Any) -> str:
        return page.content()

    def keyboard_press(self, page: Any, key: str) -> None:
        page.keyboard.press(key)

    def get_url(self, page: Any) -> str:
        return page.url

    def element_fill(self, element: Any, value: str) -> None:
        element.fill(value)
