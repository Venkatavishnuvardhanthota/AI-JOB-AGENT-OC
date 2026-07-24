from __future__ import annotations

import importlib
from datetime import datetime

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


class DesktopProvider(BaseNotificationProvider):
    name = "desktop"
    display_name = "Desktop Notification"
    description = "Delivers native desktop notifications"

    def __init__(self, config: IntegrationsConfig) -> None:
        super().__init__(config)
        self._enabled = config.desktop.enabled

    def initialize(self) -> None:
        logger.info("Desktop notification provider initialized", enabled=self._enabled)

    def validate_credentials(self) -> bool:
        return True

    def send(self, message: NotificationMessage) -> DeliveryStatus:
        if not self._enabled:
            logger.debug("Desktop notifications disabled, skipping")
            return DeliveryStatus.FAILED

        try:
            _plyer = importlib.import_module("plyer")
            _plyer.notification.notify(
                title=message.title[:256],
                message=message.body[:256],
                app_name="AI Job Agent",
                app_icon=None,
                timeout=10,
            )
            logger.info("Desktop notification sent", title=message.title)
            return DeliveryStatus.DELIVERED
        except ImportError:
            logger.warning("plyer not installed, desktop notifications unavailable")
            return DeliveryStatus.FAILED
        except Exception as e:
            logger.error("Desktop notification failed", error=str(e))
            return DeliveryStatus.FAILED

    def health(self) -> ProviderHealth:
        try:
            importlib.import_module("plyer")
            available = True
        except ImportError:
            available = False

        return ProviderHealth(
            status=ProviderStatus.HEALTHY if (self._enabled and available) else ProviderStatus.UNHEALTHY,
            message=(
                "Desktop notifications available"
                if (self._enabled and available)
                else "Desktop notifications unavailable"
            ),
            last_check=datetime.utcnow(),
            details={"enabled": self._enabled, "plyer_available": available},
        )

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            version=self.version,
            channel=DeliveryChannel.DESKTOP,
            configurable={"enabled": self._enabled},
        )
