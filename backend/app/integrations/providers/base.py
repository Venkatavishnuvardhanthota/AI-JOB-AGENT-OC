from __future__ import annotations

from abc import ABC, abstractmethod

from app.integrations.config import IntegrationsConfig
from app.integrations.schemas import (
    DeliveryStatus,
    NotificationMessage,
    ProviderHealth,
    ProviderMetadata,
)


class BaseNotificationProvider(ABC):
    name: str = ""
    display_name: str = ""
    description: str = ""
    version: str = "0.1.0"

    def __init__(self, config: IntegrationsConfig) -> None:
        self._config = config

    @abstractmethod
    def initialize(self) -> None: ...

    @abstractmethod
    def validate_credentials(self) -> bool: ...

    @abstractmethod
    def send(self, message: NotificationMessage) -> DeliveryStatus: ...

    @abstractmethod
    def health(self) -> ProviderHealth: ...

    def shutdown(self) -> None:  # noqa: B027
        pass

    @abstractmethod
    def metadata(self) -> ProviderMetadata: ...
