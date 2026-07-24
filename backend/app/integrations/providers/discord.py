from __future__ import annotations

from datetime import datetime

import requests
import structlog

from app.integrations.config import IntegrationsConfig
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


class DiscordProvider(BaseNotificationProvider):
    name = "discord"
    display_name = "Discord"
    description = "Delivers notifications via Discord webhooks"

    def __init__(self, config: IntegrationsConfig) -> None:
        super().__init__(config)
        self._session = requests.Session()

    def initialize(self) -> None:
        logger.info("Discord provider initialized")

    def validate_credentials(self) -> bool:
        webhook_url = self._config.discord.default_webhook_url
        return bool(webhook_url) and "discord.com/api/webhooks" in webhook_url

    def send(self, message: NotificationMessage) -> DeliveryStatus:
        webhook_url = message.metadata.get("webhook_url") or self._config.discord.default_webhook_url
        if not webhook_url:
            logger.warning("Discord webhook URL not configured")
            return DeliveryStatus.FAILED

        embed = self._build_embed(message)
        payload = {"content": message.title[:2000], "embeds": [embed]}

        try:
            resp = self._session.post(webhook_url, json=payload, timeout=self._config.discord.timeout_seconds)
            if resp.ok:
                logger.info("Discord notification sent")
                return DeliveryStatus.DELIVERED
            logger.warning("Discord webhook failed", status=resp.status_code, body=resp.text[:200])
            return DeliveryStatus.FAILED
        except requests.RequestException as e:
            logger.error("Discord request failed", error=str(e))
            return DeliveryStatus.FAILED

    def _build_embed(self, message: NotificationMessage) -> dict:
        color_map = {
            "critical": 0xE74C3C,
            "high": 0xF39C12,
            "normal": 0x2ECC71,
            "low": 0x95A5A6,
        }
        color = color_map.get(message.priority.value, 0x5865F2)

        embed = {
            "title": message.title[:256],
            "description": (message.body[:4096] if message.body else ""),
            "color": color,
            "timestamp": message.created_at.isoformat(),
            "footer": {"text": f"AI Job Agent · {message.type.value}"},
            "fields": [],
        }

        embed["fields"].append({"name": "Priority", "value": message.priority.value, "inline": True})
        if message.recipient:
            embed["fields"].append({"name": "Recipient", "value": message.recipient, "inline": True})

        for key in ("orchestration_id", "application_id", "provider"):
            val = message.metadata.get(key)
            if val:
                embed["fields"].append({"name": key.replace("_", " ").title(), "value": str(val), "inline": True})

        errors = message.metadata.get("errors", [])
        if errors:
            embed["fields"].append({"name": "Errors", "value": "\n".join(f"• {e}" for e in errors[:5])[:1024]})

        return embed

    def health(self) -> ProviderHealth:
        webhook_url = self._config.discord.default_webhook_url
        healthy = bool(webhook_url)
        return ProviderHealth(
            status=ProviderStatus.HEALTHY if healthy else ProviderStatus.UNHEALTHY,
            message="Discord webhook configured" if healthy else "Discord webhook not configured",
            last_check=datetime.utcnow(),
            details={"webhook_configured": bool(webhook_url)},
        )

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            version=self.version,
            channel=DeliveryChannel.DISCORD,
            supports_templates=True,
            configurable={"webhook_configured": bool(self._config.discord.default_webhook_url)},
        )
