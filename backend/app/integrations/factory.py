from __future__ import annotations

import structlog

from app.integrations.config import IntegrationsConfig
from app.integrations.providers.browser import BrowserNotificationProvider
from app.integrations.providers.console import ConsoleProvider
from app.integrations.providers.desktop import DesktopProvider
from app.integrations.providers.discord import DiscordProvider
from app.integrations.providers.email_provider import EmailProvider
from app.integrations.providers.slack import SlackProvider
from app.integrations.providers.teams import TeamsProvider
from app.integrations.providers.webhook_provider import WebhookProvider
from app.integrations.registry import ProviderRegistry

logger = structlog.get_logger(__name__)


class ProviderFactory:
    def __init__(self, registry: ProviderRegistry, config: IntegrationsConfig) -> None:
        self._registry = registry
        self._config = config

    def register_all(self) -> None:
        registrations: list[tuple[str, type]] = [
            ("console", ConsoleProvider),
            ("email", EmailProvider),
            ("webhook", WebhookProvider),
            ("slack", SlackProvider),
            ("discord", DiscordProvider),
            ("teams", TeamsProvider),
            ("browser", BrowserNotificationProvider),
            ("desktop", DesktopProvider),
        ]

        for name, provider_class in registrations:
            if name in self._config.enabled_providers and not self._registry.is_registered(name):
                provider = provider_class(self._config)
                self._registry.register(provider)

        registered = self._registry.list_providers()
        logger.info("Registered notification providers", providers=registered)

    def create_provider(self, name: str) -> object:
        mapping: dict[str, type] = {
            "console": ConsoleProvider,
            "email": EmailProvider,
            "webhook": WebhookProvider,
            "slack": SlackProvider,
            "discord": DiscordProvider,
            "teams": TeamsProvider,
            "browser": BrowserNotificationProvider,
            "desktop": DesktopProvider,
        }
        provider_class = mapping.get(name)
        if provider_class is None:
            raise ValueError(f"Unknown notification provider: {name}")
        return provider_class(self._config)
