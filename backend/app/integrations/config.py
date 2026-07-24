from __future__ import annotations

from pydantic import BaseModel, Field


class EmailConfig(BaseModel):
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    default_from: str = "noreply@aijobagent.com"
    default_from_name: str = "AI Job Agent"
    default_reply_to: str = ""
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: float = 5.0


class WebhookConfig(BaseModel):
    default_timeout_seconds: int = 10
    max_retry_attempts: int = 3
    retry_delay_seconds: float = 5.0
    backoff_multiplier: float = 2.0
    max_payload_size_kb: int = 256
    allowed_domains: list[str] = Field(default_factory=lambda: ["*"])
    hmac_enabled: bool = False
    hmac_secret: str = ""
    hmac_header: str = "X-Signature-256"


class SlackConfig(BaseModel):
    default_webhook_url: str = ""
    default_channel: str = "#notifications"
    bot_token: str = ""
    signing_secret: str = ""
    timeout_seconds: int = 10


class DiscordConfig(BaseModel):
    default_webhook_url: str = ""
    bot_token: str = ""
    timeout_seconds: int = 10


class TeamsConfig(BaseModel):
    default_webhook_url: str = ""
    timeout_seconds: int = 10


class BrowserConfig(BaseModel):
    enabled: bool = True
    max_notifications: int = 50
    ttl_seconds: int = 86400


class DesktopConfig(BaseModel):
    enabled: bool = False
    app_id: str = "ai-job-agent"


class ConsoleConfig(BaseModel):
    enabled: bool = True
    color_output: bool = True
    log_level: str = "INFO"


class IntegrationsConfig(BaseModel):
    default_provider: str = "console"
    default_channel: str = "console"
    retry_global_enabled: bool = True
    global_max_retries: int = 3
    global_retry_delay_seconds: float = 5.0
    dead_letter_enabled: bool = True
    delivery_tracking_enabled: bool = True
    health_check_interval_seconds: int = 60

    email: EmailConfig = Field(default_factory=EmailConfig)
    webhook: WebhookConfig = Field(default_factory=WebhookConfig)
    slack: SlackConfig = Field(default_factory=SlackConfig)
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    teams: TeamsConfig = Field(default_factory=TeamsConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    desktop: DesktopConfig = Field(default_factory=DesktopConfig)
    console: ConsoleConfig = Field(default_factory=ConsoleConfig)

    enabled_providers: list[str] = Field(default_factory=lambda: ["console", "email", "webhook", "slack", "discord"])
