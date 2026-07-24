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


class TeamsProvider(BaseNotificationProvider):
    name = "teams"
    display_name = "Microsoft Teams"
    description = "Delivers notifications via Microsoft Teams webhooks"

    def __init__(self, config: IntegrationsConfig) -> None:
        super().__init__(config)
        self._session = requests.Session()

    def initialize(self) -> None:
        logger.info("Teams provider initialized")

    def validate_credentials(self) -> bool:
        webhook_url = self._config.teams.default_webhook_url
        return bool(webhook_url) and "webhook" in webhook_url.lower()

    def send(self, message: NotificationMessage) -> DeliveryStatus:
        webhook_url = message.metadata.get("webhook_url") or self._config.teams.default_webhook_url
        if not webhook_url:
            logger.warning("Teams webhook URL not configured")
            return DeliveryStatus.FAILED

        card = self._build_card(message)
        payload = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": card,
                }
            ],
        }

        try:
            resp = self._session.post(webhook_url, json=payload, timeout=self._config.teams.timeout_seconds)
            if resp.ok:
                logger.info("Teams notification sent")
                return DeliveryStatus.DELIVERED
            logger.warning("Teams webhook failed", status=resp.status_code, body=resp.text[:200])
            return DeliveryStatus.FAILED
        except requests.RequestException as e:
            logger.error("Teams request failed", error=str(e))
            return DeliveryStatus.FAILED

    def _build_card(self, message: NotificationMessage) -> dict:
        color_map = {
            "critical": "Attention",
            "high": "Warning",
            "normal": "Good",
            "low": "Accent",
        }

        card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": message.title,
                    "weight": "Bolder",
                    "size": "Medium",
                    "wrap": True,
                },
            ],
            "msteams": {"width": "Full"},
        }

        if message.body:
            card["body"].append(
                {
                    "type": "TextBlock",
                    "text": message.body[:500],
                    "wrap": True,
                    "isSubtle": True,
                }
            )

        fact_set = {"type": "FactSet", "facts": []}
        fact_set["facts"].append({"title": "Type", "value": message.type.value})
        fact_set["facts"].append({"title": "Priority", "value": message.priority.value})
        if message.recipient:
            fact_set["facts"].append({"title": "Recipient", "value": message.recipient})
        for key in ("orchestration_id", "application_id", "provider"):
            val = message.metadata.get(key)
            if val:
                fact_set["facts"].append({"title": key.replace("_", " ").title(), "value": str(val)})
        card["body"].append(fact_set)

        errors = message.metadata.get("errors", [])
        if errors:
            card["body"].append(
                {
                    "type": "TextBlock",
                    "text": "Errors:\n" + "\n".join(f"• {e}" for e in errors[:5]),
                    "wrap": True,
                    "color": color_map.get("critical", "Attention"),
                }
            )

        card["body"].append(
            {
                "type": "TextBlock",
                "text": f"AI Job Agent · {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
                "isSubtle": True,
                "size": "Small",
                "wrap": True,
            }
        )

        return card

    def health(self) -> ProviderHealth:
        webhook_url = self._config.teams.default_webhook_url
        healthy = bool(webhook_url)
        return ProviderHealth(
            status=ProviderStatus.HEALTHY if healthy else ProviderStatus.UNHEALTHY,
            message="Teams webhook configured" if healthy else "Teams webhook not configured",
            last_check=datetime.utcnow(),
            details={"webhook_configured": bool(webhook_url)},
        )

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            version=self.version,
            channel=DeliveryChannel.TEAMS,
            supports_templates=True,
            configurable={"webhook_configured": bool(self._config.teams.default_webhook_url)},
        )
