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


class SlackProvider(BaseNotificationProvider):
    name = "slack"
    display_name = "Slack"
    description = "Delivers notifications via Slack webhooks"

    def __init__(self, config: IntegrationsConfig) -> None:
        super().__init__(config)
        self._session = requests.Session()

    def initialize(self) -> None:
        logger.info("Slack provider initialized")

    def validate_credentials(self) -> bool:
        webhook_url = self._config.slack.default_webhook_url
        return bool(webhook_url) and webhook_url.startswith("https://hooks.slack.com/")

    def send(self, message: NotificationMessage) -> DeliveryStatus:
        webhook_url = message.metadata.get("webhook_url") or self._config.slack.default_webhook_url
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return DeliveryStatus.FAILED

        blocks = self._build_blocks(message)
        payload = {
            "text": message.title,
            "blocks": blocks,
            "username": "AI Job Agent",
        }

        channel = message.metadata.get("channel") or self._config.slack.default_channel
        if channel:
            payload["channel"] = channel

        try:
            resp = self._session.post(webhook_url, json=payload, timeout=self._config.slack.timeout_seconds)
            if resp.ok:
                logger.info("Slack notification sent", channel=channel)
                return DeliveryStatus.DELIVERED
            logger.warning("Slack webhook failed", status=resp.status_code, body=resp.text[:200])
            return DeliveryStatus.FAILED
        except requests.RequestException as e:
            logger.error("Slack request failed", error=str(e))
            return DeliveryStatus.FAILED

    def _build_blocks(self, message: NotificationMessage) -> list[dict]:
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": message.title[:150]},
            }
        ]

        if message.body:
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": message.body[:3000]}})

        fields = []
        fields.append({"type": "mrkdwn", "text": f"*Type:*\n{message.type.value}"})
        fields.append({"type": "mrkdwn", "text": f"*Priority:*\n{message.priority.value}"})
        if message.recipient:
            fields.append({"type": "mrkdwn", "text": f"*Recipient:*\n{message.recipient}"})
        if message.metadata.get("provider"):
            fields.append({"type": "mrkdwn", "text": f"*Provider:*\n{message.metadata['provider']}"})

        if fields:
            blocks.append({"type": "section", "fields": fields})

        for key in ("orchestration_id", "application_id"):
            if message.metadata.get(key):
                blocks.append(
                    {
                        "type": "context",
                        "elements": [{"type": "mrkdwn", "text": f"*{key}:* {message.metadata[key]}"}],
                    }
                )

        if message.metadata.get("errors"):
            error_text = "\n".join(f"• {e}" for e in message.metadata["errors"])
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Errors:*\n{error_text}"},
                }
            )

        blocks.append({"type": "divider"})
        return blocks

    def health(self) -> ProviderHealth:
        webhook_url = self._config.slack.default_webhook_url
        healthy = bool(webhook_url) and webhook_url.startswith("https://hooks.slack.com/")
        return ProviderHealth(
            status=ProviderStatus.HEALTHY if healthy else ProviderStatus.UNHEALTHY,
            message="Slack webhook configured" if healthy else "Slack webhook not configured",
            last_check=datetime.utcnow(),
            details={"webhook_configured": bool(webhook_url)},
        )

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            version=self.version,
            channel=DeliveryChannel.SLACK,
            supports_templates=True,
            configurable={
                "webhook_configured": bool(self._config.slack.default_webhook_url),
                "default_channel": self._config.slack.default_channel,
            },
        )
