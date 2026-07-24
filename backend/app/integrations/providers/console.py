from __future__ import annotations

from datetime import datetime

import structlog

from app.integrations.providers.base import BaseNotificationProvider
from app.integrations.schemas import (
    DeliveryChannel,
    DeliveryStatus,
    NotificationMessage,
    ProviderHealth,
    ProviderMetadata,
    ProviderStatus,
)

logger = structlog.get_logger(__name__)


class ConsoleProvider(BaseNotificationProvider):
    name = "console"
    display_name = "Console"
    description = "Logs notifications to the console for development"

    def initialize(self) -> None:
        logger.info("Console provider initialized")

    def validate_credentials(self) -> bool:
        return True

    def send(self, message: NotificationMessage) -> DeliveryStatus:
        icon = {
            "job_discovered": "🔍",
            "job_matched": "🎯",
            "application_prepared": "📝",
            "application_submitted": "✅",
            "application_failed": "❌",
            "application_accepted": "🎉",
            "application_rejected": "💔",
            "workflow_completed": "✔️",
            "workflow_failed": "🔥",
            "manual_intervention_required": "👋",
            "orchestration_paused": "⏸️",
            "orchestration_resumed": "▶️",
            "report_generated": "📊",
            "system_warning": "⚠️",
            "system_error": "🚨",
            "custom": "📬",
        }.get(message.type.value, "📬")

        level = "info"
        if message.type.value in ("system_error", "application_failed", "workflow_failed"):
            level = "error"
        elif message.type.value in ("system_warning",):
            level = "warning"

        log_method = getattr(logger, level, logger.info)
        log_method(
            f"{icon} {message.title}",
            type=message.type.value,
            body=message.body,
            recipient=message.recipient,
            priority=message.priority.value,
        )

        if self._config.console.color_output:
            color = {
                "info": "\033[36m",
                "warning": "\033[33m",
                "error": "\033[31m",
            }.get(level, "\033[36m")
            reset = "\033[0m"
            print(f"{color}[{message.type.value.upper()}]{reset} {message.title}")
            if message.body:
                print(f"  {message.body[:200]}")
        else:
            print(f"[{message.type.value.upper()}] {message.title}")
            if message.body:
                print(f"  {message.body[:200]}")

        return DeliveryStatus.DELIVERED

    def health(self) -> ProviderHealth:
        return ProviderHealth(
            status=ProviderStatus.HEALTHY,
            message="Console provider is always healthy",
            last_check=datetime.utcnow(),
        )

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            version=self.version,
            channel=DeliveryChannel.CONSOLE,
        )
