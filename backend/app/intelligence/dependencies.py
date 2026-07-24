from __future__ import annotations

from functools import lru_cache
from threading import Lock

from app.intelligence.config import IntelligenceConfig
from app.intelligence.factory import IntelligenceFactory
from app.intelligence.registry import IntelligenceProviderRegistry
from app.intelligence.service import IntelligenceService

_service_instance: IntelligenceService | None = None
_service_lock = Lock()


@lru_cache
def _get_registry() -> IntelligenceProviderRegistry:
    return IntelligenceProviderRegistry()


@lru_cache
def _get_config() -> IntelligenceConfig:
    return IntelligenceConfig()


def get_registry() -> IntelligenceProviderRegistry:
    return _get_registry()


def get_intelligence_config() -> IntelligenceConfig:
    return _get_config()


def ensure_providers_registered() -> None:
    registry = _get_registry()
    if registry.list_analytics() or registry.list_recommendations():
        return
    config = _get_config()
    factory = IntelligenceFactory(registry, config)
    factory.register_all()


def get_intelligence_service() -> IntelligenceService:
    global _service_instance
    if _service_instance is None:
        with _service_lock:
            if _service_instance is None:
                registry = _get_registry()
                config = _get_config()
                ensure_providers_registered()
                analytics = registry.get_analytics("default") if registry.has_analytics("default") else None
                recommendations = (
                    registry.get_recommendation("default") if registry.has_recommendation("default") else None
                )
                learning = registry.get_learning("default") if registry.has_learning("default") else None
                optimization = registry.get_optimization("default") if registry.has_optimization("default") else None
                scoring = registry.get_scoring("default") if registry.has_scoring("default") else None
                feedback = registry.get_feedback("default") if registry.has_feedback("default") else None
                history_registry = registry.get_history("default") if registry.has_history("default") else None
                experiments = registry.get_experiment("default") if registry.has_experiment("default") else None
                _service_instance = IntelligenceService(
                    config=config,
                    analytics=analytics,
                    recommendations=recommendations,
                    learning=learning,
                    optimization=optimization,
                    scoring=scoring,
                    feedback=feedback,
                    history=history_registry,
                    experiments=experiments,
                )
    return _service_instance


def reset_intelligence_service() -> None:
    global _service_instance
    registry = _get_registry()
    registry.clear()
    _service_instance = None
