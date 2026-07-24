from __future__ import annotations

from datetime import datetime
from threading import Lock

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


class BrowserNotificationProvider(BaseNotificationProvider):
    name = "browser"
    display_name = "Browser Notification"
    description = "Delivers in-app browser notifications"

    def __init__(self, config: IntegrationsConfig) -> None:
        super().__init__(config)
        self._notifications: list[dict] = []
        self._lock = Lock()

    def initialize(self) -> None:
        logger.info("Browser notification provider initialized")

    def validate_credentials(self) -> bool:
        return True

    def send(self, message: NotificationMessage) -> DeliveryStatus:
        notification = {
            "id": __import__("uuid").uuid4().hex[:12],
            "type": message.type.value,
            "title": message.title,
            "body": message.body,
            "priority": message.priority.value,
            "recipient": message.recipient,
            "metadata": message.metadata,
            "created_at": message.created_at.isoformat(),
            "read": False,
        }

        with self._lock:
            self._notifications.append(notification)
            max_notifications = self._config.browser.max_notifications
            if len(self._notifications) > max_notifications:
                self._notifications = self._notifications[-max_notifications:]

        logger.info("Browser notification queued", title=message.title)
        return DeliveryStatus.DELIVERED

    def get_notifications(self, limit: int = 50) -> list[dict]:
        with self._lock:
            return list(self._notifications[-limit:])

    def mark_read(self, notification_id: str) -> bool:
        with self._lock:
            for n in self._notifications:
                if n["id"] == notification_id:
                    n["read"] = True
                    return True
        return False

    def clear(self) -> None:
        with self._lock:
            self._notifications.clear()

    def health(self) -> ProviderHealth:
        return ProviderHealth(
            status=ProviderStatus.HEALTHY,
            message="Browser notification provider is healthy",
            last_check=datetime.utcnow(),
            details={"queued_count": len(self._notifications)},
        )

    def shutdown(self) -> None:
        self.clear()

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            version=self.version,
            channel=DeliveryChannel.BROWSER,
            configurable={
                "max_notifications": self._config.browser.max_notifications,
                "ttl_seconds": self._config.browser.ttl_seconds,
            },
        )
