"""Provider health checks."""

import logging
import time
from dataclasses import dataclass
from typing import Any

from app.services.providers.base import BaseProvider
from app.services.providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health status for a single provider."""

    name: str
    available: bool
    latency_ms: float | None = None
    error: str | None = None
    last_success: float | None = None
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "available": self.available,
            "latency_ms": round(self.latency_ms, 1) if self.latency_ms is not None else None,
            "error": self.error,
            "enabled": self.enabled,
        }


async def check_provider_health(
    provider: BaseProvider,
    timeout: float = 5.0,
) -> HealthStatus:
    """Check a single provider's health by attempting to reach its base URL."""
    start = time.monotonic()
    try:
        if provider.settings.base_url:
            import httpx

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.head(
                    provider.settings.base_url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    follow_redirects=True,
                )
                latency = (time.monotonic() - start) * 1000
                available = response.status_code < 500
                return HealthStatus(
                    name=provider.name,
                    available=available,
                    latency_ms=latency,
                    error=None if available else f"HTTP {response.status_code}",
                    enabled=provider.enabled,
                )
        else:
            return HealthStatus(
                name=provider.name,
                available=True,
                latency_ms=0.0,
                enabled=provider.enabled,
            )
    except Exception as e:
        latency = (time.monotonic() - start) * 1000
        return HealthStatus(
            name=provider.name,
            available=False,
            latency_ms=latency,
            error=str(e)[:200],
            enabled=provider.enabled,
        )


async def check_all_providers(
    registry: ProviderRegistry,
    timeout: float = 5.0,
) -> list[HealthStatus]:
    """Check health of all registered providers."""
    results: list[HealthStatus] = []
    for _name, provider in registry.get_all().items():
        status = await check_provider_health(provider, timeout=timeout)
        results.append(status)
    return results


async def check_enabled_providers(
    registry: ProviderRegistry,
    timeout: float = 5.0,
) -> list[HealthStatus]:
    """Check health of only enabled providers."""
    results: list[HealthStatus] = []
    for _name, provider in registry.get_enabled().items():
        status = await check_provider_health(provider, timeout=timeout)
        results.append(status)
    return results
