from __future__ import annotations

from collections.abc import AsyncGenerator
from threading import Lock

from app.browser.dependencies import get_browser_service
from app.browser.service import BrowserService
from app.uploads.config import UploadsConfig
from app.uploads.factory import UploadProviderFactory
from app.uploads.registry import UploadProviderRegistry
from app.uploads.service import DocumentUploadService

_registry_instance: UploadProviderRegistry | None = None
_registry_lock = Lock()
_service_instance: DocumentUploadService | None = None
_service_lock = Lock()


def get_uploads_config() -> UploadsConfig:
    return UploadsConfig()


def get_uploads_registry() -> UploadProviderRegistry:
    global _registry_instance
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = UploadProviderRegistry()
    return _registry_instance


def get_uploads_factory(
    registry: UploadProviderRegistry | None = None,
    config: UploadsConfig | None = None,
) -> UploadProviderFactory:
    return UploadProviderFactory(
        registry=registry or get_uploads_registry(),
        config=config or get_uploads_config(),
    )


def get_uploads_service(
    registry: UploadProviderRegistry | None = None,
    factory: UploadProviderFactory | None = None,
    config: UploadsConfig | None = None,
    browser_service: BrowserService | None = None,
) -> DocumentUploadService:
    global _service_instance
    if _service_instance is None:
        with _service_lock:
            if _service_instance is None:
                _config = config or get_uploads_config()
                _browser = browser_service or get_browser_service()
                _registry = registry or get_uploads_registry()
                _factory = factory or get_uploads_factory(_registry, _config)
                _factory.register_all()
                _service_instance = DocumentUploadService(
                    registry=_registry,
                    factory=_factory,
                    config=_config,
                    browser_service=_browser,
                )
    return _service_instance


async def get_uploads_service_async() -> AsyncGenerator[DocumentUploadService, None]:
    service = get_uploads_service()
    try:
        yield service
    finally:
        pass


def reset_uploads_service() -> None:
    global _service_instance
    global _registry_instance
    _service_instance = None
    _registry_instance = None
