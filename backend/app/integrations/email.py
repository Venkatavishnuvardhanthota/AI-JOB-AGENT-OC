from __future__ import annotations

import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog

from app.integrations.config import IntegrationsConfig
from app.integrations.exceptions import DeliveryError
from app.integrations.schemas import EmailMessage, NotificationPriority

logger = structlog.get_logger(__name__)


class EmailSender:
    def __init__(self, config: IntegrationsConfig) -> None:
        self._config = config.email
        self._logger = logger.bind(service="email_sender")

    def send(self, message: EmailMessage) -> bool:
        try:
            msg = self._build_message(message)
            with smtplib.SMTP(
                self._config.smtp_host, self._config.smtp_port, timeout=self._config.timeout_seconds
            ) as server:
                if self._config.smtp_use_tls:
                    server.starttls()
                if self._config.smtp_user and self._config.smtp_password:
                    server.login(self._config.smtp_user, self._config.smtp_password)
                server.sendmail(self._config.default_from, message.to, msg.as_string())
            self._logger.info("Email sent", to=message.to, subject=message.subject)
            return True
        except Exception as e:
            self._logger.error("Failed to send email", to=message.to, error=str(e))
            raise DeliveryError(f"Email delivery failed: {e}") from e

    def _build_message(self, message: EmailMessage) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["From"] = self._config.default_from
        msg["To"] = ", ".join(message.to)
        msg["Subject"] = message.subject
        if message.cc:
            msg["Cc"] = ", ".join(message.cc)
        if message.reply_to:
            msg["Reply-To"] = message.reply_to

        priority_map = {
            NotificationPriority.LOW: "5 (Lowest)",
            NotificationPriority.NORMAL: "3 (Normal)",
            NotificationPriority.HIGH: "2 (High)",
            NotificationPriority.CRITICAL: "1 (Highest)",
        }
        if message.priority in priority_map:
            msg["X-Priority"] = priority_map[message.priority]

        msg.attach(MIMEText(message.body, "plain"))
        if message.html_body:
            msg.attach(MIMEText(message.html_body, "html"))

        for filepath in message.attachments:
            try:
                with open(filepath, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    filename = filepath.split("/")[-1].split("\\")[-1]
                    part.add_header("Content-Disposition", f"attachment; filename={filename}")
                    msg.attach(part)
            except OSError as e:
                self._logger.warning("Failed to attach file", filepath=filepath, error=str(e))

        return msg

    def validate_credentials(self) -> bool:
        try:
            with smtplib.SMTP(self._config.smtp_host, self._config.smtp_port, timeout=5) as server:
                if self._config.smtp_use_tls:
                    server.starttls()
                if self._config.smtp_user and self._config.smtp_password:
                    server.login(self._config.smtp_user, self._config.smtp_password)
                return True
        except Exception:
            return False
