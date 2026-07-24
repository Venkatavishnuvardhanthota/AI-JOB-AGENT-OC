from __future__ import annotations

from abc import ABC, abstractmethod

from app.integrations.schemas import (
    DeliveryStatus,
    NotificationMessage,
    ProviderHealth,
    ProviderMetadata,
)


class NotificationProvider(ABC):
    name: str
    display_name: str
    description: str = ""
    version: str = "0.1.0"

    @abstractmethod
    def initialize(self) -> None: ...

    @abstractmethod
    def validate_credentials(self) -> bool: ...

    @abstractmethod
    def send(self, message: NotificationMessage) -> DeliveryStatus: ...

    @abstractmethod
    def health(self) -> ProviderHealth: ...

    @abstractmethod
    def shutdown(self) -> None: ...

    @abstractmethod
    def metadata(self) -> ProviderMetadata: ...
