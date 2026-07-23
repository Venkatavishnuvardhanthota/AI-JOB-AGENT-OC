from __future__ import annotations

from collections.abc import AsyncGenerator

from app.forms.config import FormsConfig
from app.forms.factory import FormProviderFactory
from app.forms.registry import FormProviderRegistry
from app.forms.service import FormIntelligenceService

_registry_instance: FormProviderRegistry | None = None
_service_instance: FormIntelligenceService | None = None


def get_forms_config() -> FormsConfig:
    return FormsConfig()


def get_forms_registry() -> FormProviderRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = FormProviderRegistry()
    return _registry_instance


def get_forms_factory(
    registry: FormProviderRegistry | None = None,
    config: FormsConfig | None = None,
) -> FormProviderFactory:
    return FormProviderFactory(
        registry=registry or get_forms_registry(),
        config=config or get_forms_config(),
    )


def get_forms_service(
    registry: FormProviderRegistry | None = None,
    factory: FormProviderFactory | None = None,
    config: FormsConfig | None = None,
) -> FormIntelligenceService:
    global _service_instance
    if _service_instance is None:
        _config = config or get_forms_config()
        _registry = registry or get_forms_registry()
        _factory = factory or get_forms_factory(_registry, _config)
        _factory.register_all()
        _service_instance = FormIntelligenceService(
            registry=_registry,
            factory=_factory,
            config=_config,
        )
    return _service_instance


async def get_forms_service_async() -> AsyncGenerator[FormIntelligenceService, None]:
    service = get_forms_service()
    try:
        yield service
    finally:
        pass


def reset_forms_service() -> None:
    global _service_instance
    global _registry_instance
    _service_instance = None
    _registry_instance = None
