from __future__ import annotations

from collections.abc import AsyncGenerator
from threading import Lock

from app.submission_engine.config import SubmissionEngineConfig
from app.submission_engine.factory import SubmissionProviderFactory
from app.submission_engine.registry import SubmissionProviderRegistry
from app.submission_engine.service import SubmissionEngineService

_registry_instance: SubmissionProviderRegistry | None = None
_registry_lock = Lock()
_service_instance: SubmissionEngineService | None = None
_service_lock = Lock()


def get_submission_config() -> SubmissionEngineConfig:
    return SubmissionEngineConfig()


def get_submission_registry() -> SubmissionProviderRegistry:
    global _registry_instance
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = SubmissionProviderRegistry()
    return _registry_instance


def get_submission_factory(
    registry: SubmissionProviderRegistry | None = None,
    config: SubmissionEngineConfig | None = None,
) -> SubmissionProviderFactory:
    return SubmissionProviderFactory(
        registry=registry or get_submission_registry(),
        config=config or get_submission_config(),
    )


def get_submission_engine_service(
    registry: SubmissionProviderRegistry | None = None,
    factory: SubmissionProviderFactory | None = None,
    config: SubmissionEngineConfig | None = None,
) -> SubmissionEngineService:
    global _service_instance
    if _service_instance is None:
        with _service_lock:
            if _service_instance is None:
                _config = config or get_submission_config()
                _registry = registry or get_submission_registry()
                _factory = factory or get_submission_factory(_registry, _config)
                _factory.register_all()
                _service_instance = SubmissionEngineService(
                    registry=_registry,
                    factory=_factory,
                    config=_config,
                )
    return _service_instance


async def get_submission_engine_service_async() -> AsyncGenerator[SubmissionEngineService, None]:
    service = get_submission_engine_service()
    try:
        yield service
    finally:
        pass


def reset_submission_engine_service() -> None:
    global _service_instance
    global _registry_instance
    _service_instance = None
    _registry_instance = None
