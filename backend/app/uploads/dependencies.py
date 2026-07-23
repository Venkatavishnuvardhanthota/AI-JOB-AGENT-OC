from __future__ import annotations

from collections.abc import AsyncGenerator

from app.uploads.config import UploadsConfig
from app.uploads.factory import UploadProviderFactory
from app.uploads.registry import UploadProviderRegistry
from app.uploads.service import DocumentUploadService

_registry_instance: UploadProviderRegistry | None = None
_service_instance: DocumentUploadService | None = None


def get_uploads_config() -> UploadsConfig:
    return UploadsConfig()


def get_uploads_registry() -> UploadProviderRegistry:
    global _registry_instance
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
) -> DocumentUploadService:
    global _service_instance
    if _service_instance is None:
        _config = config or get_uploads_config()
        _registry = registry or get_uploads_registry()
        _factory = factory or get_uploads_factory(_registry, _config)
        _factory.register_all()
        _service_instance = DocumentUploadService(
            registry=_registry,
            factory=_factory,
            config=_config,
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
