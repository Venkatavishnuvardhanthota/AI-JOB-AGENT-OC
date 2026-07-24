from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime
from typing import Any

import requests
import structlog

from app.integrations.config import IntegrationsConfig
from app.integrations.exceptions import HMACSigningError
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


class WebhookProvider(BaseNotificationProvider):
    name = "webhook"
    display_name = "Webhook"
    description = "Delivers notifications via HTTP webhooks"

    def __init__(self, config: IntegrationsConfig) -> None:
        super().__init__(config)
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json", "User-Agent": "AI-Job-Agent-Webhook/1.0"})

    def initialize(self) -> None:
        logger.info("Webhook provider initialized")

    def validate_credentials(self) -> bool:
        return True

    def send(self, message: NotificationMessage) -> DeliveryStatus:
        webhook_url = message.metadata.get("webhook_url", "")
        if not webhook_url:
            logger.warning("No webhook URL configured")
            return DeliveryStatus.FAILED

        payload = self._build_payload(message)
        headers = {"Content-Type": "application/json"}

        extra_headers = message.metadata.get("headers", {})
        if isinstance(extra_headers, dict):
            headers.update(extra_headers)

        if self._config.webhook.hmac_enabled and self._config.webhook.hmac_secret:
            signature = self._sign_payload(json.dumps(payload))
            headers[self._config.webhook.hmac_header] = signature

        try:
            resp = self._session.post(
                webhook_url,
                json=payload,
                headers=headers,
                timeout=self._config.webhook.default_timeout_seconds,
            )
            if resp.ok:
                logger.info("Webhook delivered", url=webhook_url, status=resp.status_code)
                return DeliveryStatus.DELIVERED
            else:
                logger.warning("Webhook failed", url=webhook_url, status=resp.status_code, body=resp.text[:200])
                return DeliveryStatus.FAILED
        except requests.RequestException as e:
            logger.error("Webhook request failed", url=webhook_url, error=str(e))
            return DeliveryStatus.FAILED

    def _build_payload(self, message: NotificationMessage) -> dict[str, Any]:
        return {
            "event": message.type.value,
            "title": message.title,
            "body": message.body,
            "priority": message.priority.value,
            "recipient": message.recipient,
            "timestamp": message.created_at.isoformat(),
            "metadata": message.metadata,
            "template_variables": message.template_variables,
        }

    def _sign_payload(self, payload: str) -> str:
        try:
            secret = self._config.webhook.hmac_secret.encode("utf-8")
            return hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
        except Exception as e:
            raise HMACSigningError(f"Failed to sign webhook payload: {e}") from e

    def health(self) -> ProviderHealth:
        return ProviderHealth(
            status=ProviderStatus.HEALTHY,
            message="Webhook provider initialized",
            last_check=datetime.utcnow(),
        )

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            version=self.version,
            channel=DeliveryChannel.WEBHOOK,
            supports_templates=True,
            configurable={
                "timeout": self._config.webhook.default_timeout_seconds,
                "hmac_enabled": self._config.webhook.hmac_enabled,
                "max_retries": self._config.webhook.max_retry_attempts,
            },
        )
