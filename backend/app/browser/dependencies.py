from __future__ import annotations

from collections.abc import AsyncGenerator
from threading import Lock

from app.browser.config import BrowserConfig
from app.browser.service import BrowserService

_service_instance: BrowserService | None = None
_service_lock = Lock()


def get_browser_config() -> BrowserConfig:
    return BrowserConfig()


def get_browser_service(
    config: BrowserConfig | None = None,
    downloads_path: str = "downloads",
    screenshots_path: str = "screenshots",
) -> BrowserService:
    global _service_instance
    if _service_instance is None:
        with _service_lock:
            if _service_instance is None:
                _service_instance = BrowserService(
                    config=config or get_browser_config(),
                    downloads_path=downloads_path,
                    screenshots_path=screenshots_path,
                )
    return _service_instance


async def get_browser_service_async() -> AsyncGenerator[BrowserService, None]:
    service = get_browser_service()
    try:
        yield service
    finally:
        pass


def reset_browser_service() -> None:
    global _service_instance
    if _service_instance is not None:
        _service_instance.close_all()
        _service_instance = None
