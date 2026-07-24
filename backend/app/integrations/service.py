from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta
from typing import Any

import structlog

from app.integrations.config import IntegrationsConfig
from app.integrations.exceptions import (
    DeliveryError,
    ProviderNotFoundError,
    ProviderUnavailableError,
    RetryExhaustedError,
)
from app.integrations.notifications import NotificationTemplateService
from app.integrations.registry import ProviderRegistry
from app.integrations.schemas import (
    DeliveryRecord,
    DeliveryStatus,
    NotificationMessage,
    NotificationPriority,
    NotificationType,
    ProviderHealth,
    ProviderStatus,
)

logger = structlog.get_logger(__name__)


class IntegrationService:
    def __init__(
        self,
        registry: ProviderRegistry,
        config: IntegrationsConfig,
        template_service: NotificationTemplateService | None = None,
    ) -> None:
        self._registry = registry
        self._config = config
        self._template_service = template_service or NotificationTemplateService()
        self._delivery_log: list[DeliveryRecord] = []
        self._delivery_lock = threading.Lock()
        self._dead_letter: list[DeliveryRecord] = []
        self._dead_letter_lock = threading.Lock()
        self._logger = logger.bind(service="integration")

    def notify(
        self,
        message: NotificationMessage,
        provider_name: str | None = None,
    ) -> DeliveryRecord:
        provider_name = provider_name or self._config.default_provider
        channel = message.channel

        try:
            provider = self._registry.resolve(provider_name)
        except ProviderNotFoundError:
            if channel and provider_name == self._config.default_provider:
                available = self._registry.list_providers()
                if available:
                    provider = self._registry.resolve(available[0])
                    provider_name = available[0]
                    self._logger.info("Falling back to available provider", provider=provider_name)
                else:
                    raise ProviderUnavailableError("No notification providers available.") from None
            else:
                raise

        record = DeliveryRecord(
            message=message,
            provider=provider_name,
            channel=channel or provider.metadata().channel,
        )

        if message.template_name:
            try:
                rendered = self._template_service.render(message.template_name, message.template_variables)
                message.body = rendered.body_template
                message.title = rendered.subject_template
            except Exception as e:
                self._logger.warning("Template rendering failed", template=message.template_name, error=str(e))

        self._logger.info(
            "Delivering notification",
            provider=provider_name,
            type=message.type.value,
            title=message.title,
        )

        record = self._deliver_with_retry(provider, message, record)
        self._log_delivery(record)
        return record

    def notify_by_type(
        self,
        notification_type: NotificationType,
        title: str,
        body: str,
        template_variables: dict[str, str] | None = None,
        recipient: str | None = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        provider: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> DeliveryRecord:
        message = NotificationMessage(
            type=notification_type,
            title=title,
            body=body,
            template_name=notification_type.value,
            template_variables=template_variables or {},
            recipient=recipient,
            priority=priority,
            metadata=metadata or {},
        )
        return self.notify(message, provider_name=provider)

    def _deliver_with_retry(
        self,
        provider: Any,
        message: NotificationMessage,
        record: DeliveryRecord,
    ) -> DeliveryRecord:
        max_attempts = self._config.global_max_retries if self._config.retry_global_enabled else 1
        record.max_attempts = max_attempts

        for attempt in range(1, max_attempts + 1):
            record.attempts = attempt
            record.last_attempt = datetime.utcnow()
            try:
                status = provider.send(message)
                record.status = status
                if status == DeliveryStatus.DELIVERED:
                    record.delivered_at = datetime.utcnow()
                    return record
                if status == DeliveryStatus.FAILED:
                    raise DeliveryError("Provider returned failed status")
            except Exception as e:
                self._logger.warning(
                    "Delivery attempt failed",
                    provider=provider.name,
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=str(e),
                )
                record.error = str(e)
                record.status = DeliveryStatus.RETRYING if attempt < max_attempts else DeliveryStatus.FAILED

                if attempt < max_attempts:
                    delay = self._config.global_retry_delay_seconds * (2 ** (attempt - 1))
                    record.next_retry = datetime.utcnow() + timedelta(seconds=delay)
                    time.sleep(delay)

        if record.status == DeliveryStatus.FAILED:
            if self._config.dead_letter_enabled:
                record.status = DeliveryStatus.DEAD_LETTER
                self._add_dead_letter(record)
            raise RetryExhaustedError(f"All {max_attempts} delivery attempts failed for provider '{provider.name}'")

        return record

    def health(self, provider_name: str | None = None) -> dict[str, ProviderHealth]:
        targets = [provider_name] if provider_name else self._registry.list_providers()
        results: dict[str, ProviderHealth] = {}
        for name in targets:
            try:
                provider = self._registry.resolve(name)
                results[name] = provider.health()
            except ProviderNotFoundError:
                results[name] = ProviderHealth(
                    status=ProviderStatus.UNHEALTHY,
                    message=f"Provider '{name}' not found",
                )
            except Exception as e:
                results[name] = ProviderHealth(
                    status=ProviderStatus.UNHEALTHY,
                    message=str(e),
                )
        return results

    def list_providers(self) -> list[str]:
        return self._registry.list_providers()

    def list_provider_details(self) -> list[dict]:
        return self._registry.list_details()

    def get_delivery_log(self, limit: int = 50) -> list[DeliveryRecord]:
        with self._delivery_lock:
            return list(self._delivery_log[-limit:])

    def get_dead_letter_queue(self) -> list[DeliveryRecord]:
        with self._dead_letter_lock:
            return list(self._dead_letter)

    def retry_dead_letter(self, record_id: str) -> DeliveryRecord | None:
        with self._dead_letter_lock:
            for i, record in enumerate(self._dead_letter):
                if record.id == record_id:
                    self._dead_letter.pop(i)
                    break
            else:
                return None
        message = record.message
        record.status = DeliveryStatus.PENDING
        record.attempts = 0
        record.error = None
        try:
            return self.notify(message, provider_name=record.provider)
        except Exception as e:
            record.status = DeliveryStatus.DEAD_LETTER
            record.error = str(e)
            self._add_dead_letter(record)
            return record

    def _log_delivery(self, record: DeliveryRecord) -> None:
        with self._delivery_lock:
            self._delivery_log.append(record)

    def _add_dead_letter(self, record: DeliveryRecord) -> None:
        with self._dead_letter_lock:
            self._dead_letter.append(record)
            self._logger.warning(
                "Notification moved to dead letter queue",
                provider=record.provider,
                error=record.error,
            )
