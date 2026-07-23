from __future__ import annotations

from collections.abc import AsyncGenerator
from threading import Lock

import structlog

from app.ats.config import ATSConfig
from app.ats.factory import ATSProviderFactory
from app.ats.registry import ATSProviderRegistry
from app.ats.service import ATSService
from app.browser.dependencies import get_browser_service
from app.browser.service import BrowserService

logger = structlog.get_logger(__name__)

_registry_instance: ATSProviderRegistry | None = None
_registry_lock = Lock()
_service_instance: ATSService | None = None
_service_lock = Lock()


def get_ats_config() -> ATSConfig:
    return ATSConfig()


def get_ats_registry() -> ATSProviderRegistry:
    global _registry_instance
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = ATSProviderRegistry()
    return _registry_instance


def get_ats_factory(
    registry: ATSProviderRegistry | None = None,
    config: ATSConfig | None = None,
    browser: BrowserService | None = None,
) -> ATSProviderFactory:
    return ATSProviderFactory(
        registry=registry or get_ats_registry(),
        config=config or get_ats_config(),
        browser=browser or get_browser_service(),
    )


def get_ats_service(
    registry: ATSProviderRegistry | None = None,
    factory: ATSProviderFactory | None = None,
    config: ATSConfig | None = None,
    browser: BrowserService | None = None,
) -> ATSService:
    global _service_instance
    if _service_instance is None:
        with _service_lock:
            if _service_instance is None:
                _config = config or get_ats_config()
                _browser = browser or get_browser_service()
                _registry = registry or get_ats_registry()
                _factory = factory or get_ats_factory(_registry, _config, _browser)
                _factory.register_all()
                _service_instance = ATSService(
                    registry=_registry,
                    factory=_factory,
                    config=_config,
                    browser=_browser,
                )
    return _service_instance


async def get_ats_service_async() -> AsyncGenerator[ATSService, None]:
    service = get_ats_service()
    try:
        yield service
    finally:
        pass


def reset_ats_service() -> None:
    global _service_instance
    global _registry_instance
    _service_instance = None
    _registry_instance = None
