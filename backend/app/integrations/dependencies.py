from __future__ import annotations

from threading import Lock

from app.integrations.config import IntegrationsConfig
from app.integrations.factory import ProviderFactory
from app.integrations.notifications import NotificationTemplateService
from app.integrations.registry import ProviderRegistry
from app.integrations.service import IntegrationService

_registry_instance: ProviderRegistry | None = None
_registry_lock = Lock()
_service_instance: IntegrationService | None = None
_service_lock = Lock()


def get_integrations_config() -> IntegrationsConfig:
    return IntegrationsConfig()


def get_provider_registry() -> ProviderRegistry:
    global _registry_instance
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = ProviderRegistry()
    return _registry_instance


def get_template_service() -> NotificationTemplateService:
    return NotificationTemplateService()


def get_integration_service(
    registry: ProviderRegistry | None = None,
    config: IntegrationsConfig | None = None,
) -> IntegrationService:
    global _service_instance
    if _service_instance is None:
        with _service_lock:
            if _service_instance is None:
                _config = config or get_integrations_config()
                _registry = registry or get_provider_registry()
                _factory = ProviderFactory(_registry, _config)
                if _registry.count() == 0:
                    _factory.register_all()
                _service_instance = IntegrationService(
                    registry=_registry,
                    config=_config,
                    template_service=get_template_service(),
                )
    return _service_instance


def reset_integration_service() -> None:
    global _service_instance, _registry_instance
    _service_instance = None
    _registry_instance = None
