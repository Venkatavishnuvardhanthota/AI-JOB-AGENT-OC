from __future__ import annotations

from datetime import datetime

import structlog

from app.integrations.config import IntegrationsConfig
from app.integrations.email import EmailSender
from app.integrations.providers.base import BaseNotificationProvider
from app.integrations.schemas import (
    DeliveryChannel,
    DeliveryStatus,
    EmailMessage,
    NotificationMessage,
    ProviderHealth,
    ProviderMetadata,
    ProviderStatus,
)

logger = structlog.get_logger(__name__)


class EmailProvider(BaseNotificationProvider):
    name = "email"
    display_name = "Email (SMTP)"
    description = "Delivers notifications via SMTP email"

    def __init__(self, config: IntegrationsConfig) -> None:
        super().__init__(config)
        self._sender = EmailSender(config)
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True
        logger.info("Email provider initialized", host=self._config.email.smtp_host)

    def validate_credentials(self) -> bool:
        return self._sender.validate_credentials()

    def send(self, message: NotificationMessage) -> DeliveryStatus:
        if not self._initialized:
            self.initialize()

        recipient = message.recipient or self._config.email.default_from
        email_msg = EmailMessage(
            to=[recipient],
            subject=message.title,
            body=message.body,
            html_body=None,
            priority=message.priority,
        )

        if message.template_variables and message.template_name:
            from app.integrations.notifications import NotificationTemplateService

            try:
                rendered = NotificationTemplateService().render(message.template_name, message.template_variables)
                email_msg.body = rendered.body_template
                email_msg.subject = rendered.subject_template
                email_msg.html_body = rendered.html_template
            except Exception:
                pass

        try:
            self._sender.send(email_msg)
            return DeliveryStatus.DELIVERED
        except Exception as e:
            logger.error("Email delivery failed", error=str(e), recipient=recipient)
            return DeliveryStatus.FAILED

    def health(self) -> ProviderHealth:
        start = datetime.utcnow()
        healthy = self.validate_credentials()
        elapsed = (datetime.utcnow() - start).total_seconds() * 1000
        return ProviderHealth(
            status=ProviderStatus.HEALTHY if healthy else ProviderStatus.UNHEALTHY,
            message="SMTP server reachable" if healthy else "SMTP server unreachable",
            last_check=datetime.utcnow(),
            response_time_ms=elapsed,
            details={"host": self._config.email.smtp_host, "port": self._config.email.smtp_port},
        )

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            version=self.version,
            channel=DeliveryChannel.EMAIL,
            supports_templates=True,
            supports_attachments=True,
            supports_priority=True,
            configurable={
                "host": self._config.email.smtp_host,
                "port": self._config.email.smtp_port,
                "use_tls": self._config.email.smtp_use_tls,
            },
        )
