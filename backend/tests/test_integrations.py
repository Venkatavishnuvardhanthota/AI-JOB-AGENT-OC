from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from app.integrations.config import (
    BrowserConfig,
    ConsoleConfig,
    DesktopConfig,
    DiscordConfig,
    EmailConfig,
    IntegrationsConfig,
    SlackConfig,
    TeamsConfig,
    WebhookConfig,
)
from app.integrations.dependencies import (
    get_integration_service,
    get_integrations_config,
    get_provider_registry,
    reset_integration_service,
)
from app.integrations.email import EmailSender
from app.integrations.exceptions import (
    ConfigurationError,
    CredentialValidationError,
    DeadLetterError,
    DeliveryError,
    HMACSigningError,
    IntegrationError,
    ProviderDuplicateError,
    ProviderNotFoundError,
    ProviderUnavailableError,
    RetryExhaustedError,
    TemplateNotFoundError,
    TemplateRenderError,
)
from app.integrations.factory import ProviderFactory
from app.integrations.interfaces import NotificationProvider
from app.integrations.notifications import NotificationTemplateService
from app.integrations.providers.base import BaseNotificationProvider
from app.integrations.providers.browser import BrowserNotificationProvider
from app.integrations.providers.console import ConsoleProvider
from app.integrations.providers.desktop import DesktopProvider
from app.integrations.providers.discord import DiscordProvider
from app.integrations.providers.email_provider import EmailProvider
from app.integrations.providers.slack import SlackProvider
from app.integrations.providers.teams import TeamsProvider
from app.integrations.providers.webhook_provider import WebhookProvider
from app.integrations.registry import ProviderRegistry
from app.integrations.schemas import (
    DeliveryChannel,
    DeliveryRecord,
    DeliveryStatus,
    EmailMessage,
    NotificationMessage,
    NotificationPriority,
    NotificationTemplate,
    NotificationType,
    ProviderHealth,
    ProviderMetadata,
    ProviderStatus,
    RichMessage,
    WebhookPayload,
)
from app.integrations.service import IntegrationService

# ── Mock Providers ──


class MockNotificationProvider(BaseNotificationProvider):
    name = "mock"
    display_name = "Mock Provider"
    description = "A mock provider for testing"

    def initialize(self) -> None:
        pass

    def validate_credentials(self) -> bool:
        return True

    def send(self, message: NotificationMessage) -> DeliveryStatus:
        return DeliveryStatus.DELIVERED

    def health(self) -> ProviderHealth:
        return ProviderHealth(status=ProviderStatus.HEALTHY, message="Mock is healthy")

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            version=self.version,
            channel=DeliveryChannel.CONSOLE,
        )


class FailingMockNotificationProvider(BaseNotificationProvider):
    name = "failing"
    display_name = "Failing Provider"
    description = "Always fails"

    def initialize(self) -> None:
        pass

    def validate_credentials(self) -> bool:
        return False

    def send(self, message: NotificationMessage) -> DeliveryStatus:
        return DeliveryStatus.FAILED

    def health(self) -> ProviderHealth:
        return ProviderHealth(status=ProviderStatus.UNHEALTHY, message="Failing is unhealthy")

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            name=self.name,
            display_name=self.display_name,
            description=self.description,
            version=self.version,
            channel=DeliveryChannel.CONSOLE,
        )


class EmptyMockProvider(BaseNotificationProvider):
    name = ""
    display_name = "Empty"

    def initialize(self) -> None:
        pass

    def validate_credentials(self) -> bool:
        return False

    def send(self, message: NotificationMessage) -> DeliveryStatus:
        raise NotImplementedError

    def health(self) -> ProviderHealth:
        return ProviderHealth(status=ProviderStatus.UNHEALTHY)

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(name=self.name, display_name=self.display_name)


# ── Fixtures ──


@pytest.fixture
def config() -> IntegrationsConfig:
    return IntegrationsConfig(
        default_provider="mock",
        retry_global_enabled=False,
        dead_letter_enabled=True,
    )


@pytest.fixture
def registry() -> ProviderRegistry:
    r = ProviderRegistry()
    r.register(MockNotificationProvider(IntegrationsConfig()))
    return r


@pytest.fixture
def registry_with_failing() -> ProviderRegistry:
    r = ProviderRegistry()
    r.register(MockNotificationProvider(IntegrationsConfig()))
    r.register(FailingMockNotificationProvider(IntegrationsConfig()))
    return r


@pytest.fixture
def service(registry: ProviderRegistry, config: IntegrationsConfig) -> IntegrationService:
    return IntegrationService(registry=registry, config=config)


@pytest.fixture
def service_with_failing(registry_with_failing: ProviderRegistry, config: IntegrationsConfig) -> IntegrationService:
    return IntegrationService(registry=registry_with_failing, config=config)


@pytest.fixture
def template_service() -> NotificationTemplateService:
    return NotificationTemplateService()


@pytest.fixture
def sample_message() -> NotificationMessage:
    return NotificationMessage(
        type=NotificationType.JOB_DISCOVERED,
        title="Test Job Found",
        body="A test job was found.",
        template_variables={
            "position": "Engineer",
            "company": "Acme",
            "location": "Remote",
            "job_url": "https://example.com/job/1",
        },
    )


# ── Enum / Schema Tests ──


class TestNotificationType:
    def test_values(self):
        assert NotificationType.JOB_DISCOVERED.value == "job_discovered"
        assert NotificationType.CUSTOM.value == "custom"

    def test_sixteen_values(self):
        values = [m.value for m in NotificationType]
        assert len(values) == 16


class TestDeliveryChannel:
    def test_values(self):
        assert DeliveryChannel.EMAIL.value == "email"
        assert DeliveryChannel.CONSOLE.value == "console"

    def test_eight_channels(self):
        assert len(list(DeliveryChannel)) == 8


class TestProviderStatus:
    def test_values(self):
        assert ProviderStatus.HEALTHY.value == "healthy"
        assert ProviderStatus.UNHEALTHY.value == "unhealthy"


class TestDeliveryStatus:
    def test_values(self):
        assert DeliveryStatus.DELIVERED.value == "delivered"
        assert DeliveryStatus.DEAD_LETTER.value == "dead_letter"


class TestNotificationPriority:
    def test_values(self):
        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.CRITICAL.value == "critical"


class TestNotificationMessage:
    def test_defaults(self):
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="T", body="B")
        assert msg.priority == NotificationPriority.NORMAL
        assert msg.recipient is None
        assert msg.template_variables == {}
        assert msg.attachments == []
        assert msg.metadata == {}

    def test_full_message(self):
        msg = NotificationMessage(
            type=NotificationType.SYSTEM_ERROR,
            title="Error",
            body="Something broke",
            priority=NotificationPriority.CRITICAL,
            recipient="admin@example.com",
            channel=DeliveryChannel.EMAIL,
            template_name="system_error",
            template_variables={"component": "db", "error": "timeout"},
            attachments=["/tmp/log.txt"],
            metadata={"source": "test"},
            provider="email",
        )
        assert msg.type == NotificationType.SYSTEM_ERROR
        assert msg.priority == NotificationPriority.CRITICAL
        assert msg.channel == DeliveryChannel.EMAIL
        assert msg.provider == "email"


class TestProviderMetadata:
    def test_defaults(self):
        m = ProviderMetadata(name="test", display_name="Test", channel=DeliveryChannel.CONSOLE)
        assert m.description == ""
        assert m.version == "0.1.0"
        assert m.supports_templates is False
        assert m.configurable == {}


class TestProviderHealth:
    def test_defaults(self):
        h = ProviderHealth()
        assert h.status == ProviderStatus.UNHEALTHY
        assert h.message == ""
        assert h.details == {}

    def test_healthy(self):
        h = ProviderHealth(status=ProviderStatus.HEALTHY, message="OK")
        assert h.status == ProviderStatus.HEALTHY


class TestDeliveryRecord:
    def test_defaults(self):
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="T", body="B")
        r = DeliveryRecord(message=msg, provider="mock", channel=DeliveryChannel.CONSOLE)
        assert r.status == DeliveryStatus.PENDING
        assert r.attempts == 0
        assert r.max_attempts == 3
        assert r.error is None

    def test_id_generated(self):
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="T", body="B")
        r = DeliveryRecord(message=msg, provider="mock", channel=DeliveryChannel.CONSOLE)
        assert len(r.id) == 12


class TestNotificationTemplate:
    def test_defaults(self):
        t = NotificationTemplate(name="test", body_template="Hello {{name}}")
        assert t.subject_template == ""
        assert t.html_template is None
        assert t.channel is None
        assert t.variables == []


class TestEmailMessage:
    def test_defaults(self):
        e = EmailMessage(to=["user@test.com"], subject="Test", body="Body")
        assert e.cc == []
        assert e.bcc == []
        assert e.reply_to is None
        assert e.attachments == []
        assert e.priority == NotificationPriority.NORMAL


class TestWebhookPayload:
    def test_defaults(self):
        w = WebhookPayload(url="https://example.com/hook")
        assert w.method == "POST"
        assert w.headers == {}
        assert w.body == {}
        assert w.hmac_header == "X-Signature-256"


class TestRichMessage:
    def test_defaults(self):
        r = RichMessage(title="Test")
        assert r.description == ""
        assert r.fields == []
        assert r.errors == []


# ── Config Tests ──


class TestEmailConfig:
    def test_defaults(self):
        c = EmailConfig()
        assert c.smtp_host == "localhost"
        assert c.smtp_port == 587
        assert c.smtp_use_tls is True
        assert c.default_from == "noreply@aijobagent.com"
        assert c.timeout_seconds == 30


class TestWebhookConfig:
    def test_defaults(self):
        c = WebhookConfig()
        assert c.default_timeout_seconds == 10
        assert c.max_retry_attempts == 3
        assert c.hmac_enabled is False


class TestIntegrationsConfig:
    def test_defaults(self):
        c = IntegrationsConfig()
        assert c.default_provider == "console"
        assert c.retry_global_enabled is True
        assert c.dead_letter_enabled is True
        assert "console" in c.enabled_providers

    def test_nested_configs(self):
        c = IntegrationsConfig()
        assert isinstance(c.email, EmailConfig)
        assert isinstance(c.webhook, WebhookConfig)
        assert isinstance(c.slack, SlackConfig)
        assert isinstance(c.discord, DiscordConfig)
        assert isinstance(c.teams, TeamsConfig)
        assert isinstance(c.browser, BrowserConfig)
        assert isinstance(c.desktop, DesktopConfig)
        assert isinstance(c.console, ConsoleConfig)

    def test_custom_providers(self):
        c = IntegrationsConfig(enabled_providers=["console", "email"])
        assert c.enabled_providers == ["console", "email"]


# ── Exception Tests ──


class TestIntegrationExceptions:
    def test_exception_hierarchy(self):
        assert issubclass(ProviderNotFoundError, IntegrationError)
        assert issubclass(ProviderUnavailableError, IntegrationError)
        assert issubclass(ProviderDuplicateError, IntegrationError)
        assert issubclass(DeliveryError, IntegrationError)
        assert issubclass(ConfigurationError, IntegrationError)
        assert issubclass(CredentialValidationError, IntegrationError)
        assert issubclass(TemplateNotFoundError, IntegrationError)
        assert issubclass(TemplateRenderError, IntegrationError)
        assert issubclass(RetryExhaustedError, IntegrationError)
        assert issubclass(DeadLetterError, IntegrationError)
        assert issubclass(HMACSigningError, IntegrationError)

    def test_exception_codes(self):
        assert IntegrationError().code == "INTEGRATION_ERROR"
        assert ProviderNotFoundError().code == "PROVIDER_NOT_FOUND"
        assert ProviderDuplicateError().code == "PROVIDER_DUPLICATE"
        assert DeliveryError().code == "DELIVERY_ERROR"
        assert RetryExhaustedError().code == "RETRY_EXHAUSTED"
        assert HMACSigningError().code == "HMAC_SIGNING_ERROR"

    def test_exception_status_codes(self):
        assert IntegrationError().status_code == 502
        assert ProviderNotFoundError().status_code == 404
        assert ProviderDuplicateError().status_code == 409
        assert ConfigurationError().status_code == 500
        assert CredentialValidationError().status_code == 401

    def test_exception_with_message(self):
        exc = DeliveryError("Custom message")
        assert str(exc) == "Custom message"


# ── NotificationTemplateService Tests ──


class TestNotificationTemplateService:
    def test_get_existing(self, template_service):
        t = template_service.get("job_discovered")
        assert t.name == "job_discovered"
        assert "{{position}}" in t.subject_template

    def test_get_nonexistent(self, template_service):
        with pytest.raises(TemplateNotFoundError):
            template_service.get("nonexistent")

    def test_list(self, template_service):
        names = template_service.list()
        assert "job_discovered" in names
        assert "custom" in names
        assert len(names) == 16

    def test_render(self, template_service):
        result = template_service.render("job_discovered", {"position": "Engineer", "company": "Acme"})
        assert "Engineer" in result.subject_template
        assert "Acme" in result.body_template
        assert result.html_template is not None
        assert "Engineer" in result.html_template

    def test_render_missing_variable(self, template_service):
        result = template_service.render("job_discovered", {})
        assert "{{position}}" in result.subject_template

    def test_render_nonexistent(self, template_service):
        with pytest.raises(TemplateNotFoundError):
            template_service.render("nonexistent", {})

    def test_render_custom_template(self, template_service):
        result = template_service.render("custom", {"subject": "Hello", "body": "World"})
        assert result.subject_template == "Hello"
        assert result.body_template == "World"


# ── Provider Registry Tests ──


class TestProviderRegistry:
    def test_register_and_resolve(self, registry: ProviderRegistry):
        assert registry.is_registered("mock")
        provider = registry.resolve("mock")
        assert provider.name == "mock"

    def test_resolve_nonexistent(self, registry: ProviderRegistry):
        with pytest.raises(ProviderNotFoundError):
            registry.resolve("nonexistent")

    def test_register_duplicate_overwrites(self, registry: ProviderRegistry):
        new_mock = MockNotificationProvider(IntegrationsConfig())
        registry.register_or_replace(new_mock)
        assert registry.count() == 1

    def test_register_empty_name_raises(self):
        r = ProviderRegistry()
        with pytest.raises(ConfigurationError):
            r.register(EmptyMockProvider(IntegrationsConfig()))

    def test_register_or_replace_empty_name_raises(self):
        r = ProviderRegistry()
        with pytest.raises(ConfigurationError):
            r.register_or_replace(EmptyMockProvider(IntegrationsConfig()))

    def test_unregister(self, registry: ProviderRegistry):
        registry.unregister("mock")
        assert not registry.is_registered("mock")
        assert registry.count() == 0

    def test_unregister_nonexistent(self, registry: ProviderRegistry):
        with pytest.raises(ProviderNotFoundError):
            registry.unregister("nonexistent")

    def test_list_providers(self, registry: ProviderRegistry):
        names = registry.list_providers()
        assert "mock" in names

    def test_list_details(self, registry: ProviderRegistry):
        details = registry.list_details()
        assert len(details) == 1
        assert details[0]["name"] == "mock"

    def test_count(self, registry: ProviderRegistry):
        assert registry.count() == 1

    def test_clear(self, registry: ProviderRegistry):
        registry.clear()
        assert registry.count() == 0

    def test_thread_safety(self, registry: ProviderRegistry):
        import concurrent.futures

        def resolve_mock():
            return registry.resolve("mock")

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            futures = [ex.submit(resolve_mock) for _ in range(100)]
            for f in concurrent.futures.as_completed(futures):
                provider = f.result()
                assert provider.name == "mock"


# ── Provider Factory Tests ──


class TestProviderFactory:
    def test_register_all(self):
        reg = ProviderRegistry()
        cfg = IntegrationsConfig(enabled_providers=["console", "mock"])
        factory = ProviderFactory(reg, cfg)
        # mock is not in the real mapping, so only console gets registered
        factory.register_all()
        assert reg.is_registered("console")

    def test_create_provider(self):
        reg = ProviderRegistry()
        cfg = IntegrationsConfig()
        factory = ProviderFactory(reg, cfg)
        provider = factory.create_provider("console")
        assert isinstance(provider, ConsoleProvider)

    def test_create_provider_unknown(self):
        reg = ProviderRegistry()
        cfg = IntegrationsConfig()
        factory = ProviderFactory(reg, cfg)
        with pytest.raises(ValueError):
            factory.create_provider("nonexistent")


# ── IntegrationService Tests ──


class TestIntegrationService:
    def test_notify_success(self, service: IntegrationService, sample_message: NotificationMessage):
        record = service.notify(sample_message)
        assert record.status == DeliveryStatus.DELIVERED
        assert record.provider == "mock"
        assert record.attempts >= 1

    def test_notify_by_type(self, service: IntegrationService):
        record = service.notify_by_type(
            notification_type=NotificationType.SYSTEM_WARNING,
            title="Warning",
            body="Something needs attention",
            template_variables={"component": "db", "message": "slow query", "severity": "warning"},
            priority=NotificationPriority.HIGH,
        )
        assert record.status == DeliveryStatus.DELIVERED
        assert record.message.type == NotificationType.SYSTEM_WARNING

    def test_notify_nonexistent_provider(self, service: IntegrationService, sample_message: NotificationMessage):
        with pytest.raises(ProviderNotFoundError):
            service.notify(sample_message, provider_name="nonexistent")

    def test_notify_with_template_rendering(self, service: IntegrationService):
        record = service.notify_by_type(
            notification_type=NotificationType.JOB_DISCOVERED,
            title="Original",
            body="Original body",
            template_variables={
                "position": "Engineer",
                "company": "Acme",
                "location": "Remote",
                "job_url": "https://example.com/job/1",
            },
        )
        assert record.status == DeliveryStatus.DELIVERED

    def test_list_providers(self, service: IntegrationService):
        providers = service.list_providers()
        assert "mock" in providers

    def test_list_provider_details(self, service: IntegrationService):
        details = service.list_provider_details()
        assert len(details) >= 1

    def test_health_all(self, service: IntegrationService):
        results = service.health()
        assert "mock" in results
        assert results["mock"].status == ProviderStatus.HEALTHY

    def test_health_specific(self, service: IntegrationService):
        results = service.health(provider_name="mock")
        assert results["mock"].status == ProviderStatus.HEALTHY

    def test_health_nonexistent(self, service: IntegrationService):
        results = service.health(provider_name="nonexistent")
        assert results["nonexistent"].status == ProviderStatus.UNHEALTHY

    def test_health_failing(self, service_with_failing: IntegrationService):
        results = service_with_failing.health()
        assert results["mock"].status == ProviderStatus.HEALTHY
        assert results["failing"].status == ProviderStatus.UNHEALTHY

    def test_delivery_log(self, service: IntegrationService, sample_message: NotificationMessage):
        service.notify(sample_message)
        log = service.get_delivery_log()
        assert len(log) == 1
        assert log[0].provider == "mock"

    def test_delivery_log_limit(self, service: IntegrationService, sample_message: NotificationMessage):
        for _ in range(5):
            service.notify(sample_message)
        log = service.get_delivery_log(limit=2)
        assert len(log) == 2


# ── Retry / Dead Letter Tests ──


class TestRetryAndDeadLetter:
    def test_retry_exhausted_moves_to_dead_letter(self, config: IntegrationsConfig):
        config.retry_global_enabled = True
        config.global_max_retries = 2
        config.dead_letter_enabled = True
        reg = ProviderRegistry()
        reg.register(FailingMockNotificationProvider(IntegrationsConfig()))
        svc = IntegrationService(registry=reg, config=config)
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="Fail", body="Will fail")
        with pytest.raises(RetryExhaustedError):
            svc.notify(msg, provider_name="failing")
        dead_letters = svc.get_dead_letter_queue()
        assert len(dead_letters) == 1

    def test_dead_letter_queue_empty_initially(self, service: IntegrationService):
        assert service.get_dead_letter_queue() == []

    def test_retry_dead_letter(self, config: IntegrationsConfig):
        config.retry_global_enabled = True
        config.global_max_retries = 1
        config.dead_letter_enabled = True
        reg = ProviderRegistry()
        reg.register(FailingMockNotificationProvider(IntegrationsConfig()))
        svc = IntegrationService(registry=reg, config=config)
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="Fail", body="Will fail")
        with pytest.raises(RetryExhaustedError):
            svc.notify(msg, provider_name="failing")
        dead_letters = svc.get_dead_letter_queue()
        assert len(dead_letters) == 1
        result = svc.retry_dead_letter(dead_letters[0].id)
        assert result is not None

    def test_retry_dead_letter_nonexistent(self, service: IntegrationService):
        result = service.retry_dead_letter("nonexistent")
        assert result is None


# ── Provider Implementation Tests ──


class TestConsoleProvider:
    def test_initialize(self):
        p = ConsoleProvider(IntegrationsConfig())
        p.initialize()

    def test_validate_credentials(self):
        p = ConsoleProvider(IntegrationsConfig())
        assert p.validate_credentials() is True

    def test_send(self):
        p = ConsoleProvider(IntegrationsConfig())
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="Test", body="Body")
        status = p.send(msg)
        assert status == DeliveryStatus.DELIVERED

    def test_health(self):
        p = ConsoleProvider(IntegrationsConfig())
        h = p.health()
        assert h.status == ProviderStatus.HEALTHY

    def test_metadata(self):
        p = ConsoleProvider(IntegrationsConfig())
        m = p.metadata()
        assert m.channel == DeliveryChannel.CONSOLE

    def test_send_error_type(self):
        p = ConsoleProvider(IntegrationsConfig())
        msg = NotificationMessage(type=NotificationType.SYSTEM_ERROR, title="Err", body="Oops")
        status = p.send(msg)
        assert status == DeliveryStatus.DELIVERED

    def test_shutdown(self):
        p = ConsoleProvider(IntegrationsConfig())
        p.shutdown()


class TestBrowserNotificationProvider:
    def test_initialize(self):
        p = BrowserNotificationProvider(IntegrationsConfig())
        p.initialize()

    def test_send(self):
        p = BrowserNotificationProvider(IntegrationsConfig())
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="Test", body="Body")
        status = p.send(msg)
        assert status == DeliveryStatus.DELIVERED

    def test_get_notifications(self):
        p = BrowserNotificationProvider(IntegrationsConfig())
        p.send(NotificationMessage(type=NotificationType.CUSTOM, title="N1", body="B1"))
        p.send(NotificationMessage(type=NotificationType.CUSTOM, title="N2", body="B2"))
        notifs = p.get_notifications()
        assert len(notifs) == 2

    def test_mark_read(self):
        p = BrowserNotificationProvider(IntegrationsConfig())
        p.send(NotificationMessage(type=NotificationType.CUSTOM, title="N1", body="B1"))
        notifs = p.get_notifications()
        nid = notifs[0]["id"]
        assert p.mark_read(nid) is True
        assert p.mark_read("nonexistent") is False

    def test_clear(self):
        p = BrowserNotificationProvider(IntegrationsConfig())
        p.send(NotificationMessage(type=NotificationType.CUSTOM, title="N1", body="B1"))
        p.clear()
        assert len(p.get_notifications()) == 0

    def test_health(self):
        p = BrowserNotificationProvider(IntegrationsConfig())
        h = p.health()
        assert h.status == ProviderStatus.HEALTHY

    def test_shutdown(self):
        p = BrowserNotificationProvider(IntegrationsConfig())
        p.send(NotificationMessage(type=NotificationType.CUSTOM, title="N1", body="B1"))
        p.shutdown()
        assert len(p.get_notifications()) == 0

    def test_max_notifications(self):
        cfg = IntegrationsConfig()
        cfg.browser.max_notifications = 3
        p = BrowserNotificationProvider(cfg)
        for i in range(5):
            p.send(NotificationMessage(type=NotificationType.CUSTOM, title=f"N{i}", body=f"B{i}"))
        assert len(p.get_notifications()) == 3


class TestDesktopProvider:
    def test_initialize(self):
        p = DesktopProvider(IntegrationsConfig())
        p.initialize()

    def test_validate_credentials(self):
        p = DesktopProvider(IntegrationsConfig())
        assert p.validate_credentials() is True

    def test_send_disabled(self):
        cfg = IntegrationsConfig()
        cfg.desktop.enabled = False
        p = DesktopProvider(cfg)
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="Test", body="Body")
        status = p.send(msg)
        assert status == DeliveryStatus.FAILED

    def test_health_disabled(self):
        p = DesktopProvider(IntegrationsConfig())
        h = p.health()
        assert h.status == ProviderStatus.UNHEALTHY

    def test_metadata(self):
        p = DesktopProvider(IntegrationsConfig())
        m = p.metadata()
        assert m.channel == DeliveryChannel.DESKTOP

    def test_shutdown(self):
        p = DesktopProvider(IntegrationsConfig())
        p.shutdown()


class TestEmailProvider:
    def test_initialize(self):
        p = EmailProvider(IntegrationsConfig())
        p.initialize()

    def test_validate_credentials_no_server(self):
        p = EmailProvider(IntegrationsConfig())
        assert p.validate_credentials() is False

    def test_send_fails_no_server(self):
        p = EmailProvider(IntegrationsConfig())
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="Test", body="Body", recipient="test@test.com")
        status = p.send(msg)
        assert status == DeliveryStatus.FAILED

    def test_health_no_server(self):
        p = EmailProvider(IntegrationsConfig())
        h = p.health()
        assert h.status == ProviderStatus.UNHEALTHY

    def test_metadata(self):
        p = EmailProvider(IntegrationsConfig())
        m = p.metadata()
        assert m.channel == DeliveryChannel.EMAIL
        assert m.supports_templates is True
        assert m.supports_attachments is True
        assert m.supports_priority is True


class TestWebhookProvider:
    def test_initialize(self):
        p = WebhookProvider(IntegrationsConfig())
        p.initialize()

    def test_validate_credentials(self):
        p = WebhookProvider(IntegrationsConfig())
        assert p.validate_credentials() is True

    def test_send_no_url(self):
        p = WebhookProvider(IntegrationsConfig())
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="Test", body="Body")
        status = p.send(msg)
        assert status == DeliveryStatus.FAILED

    def test_send_with_url(self):
        p = WebhookProvider(IntegrationsConfig())
        msg = NotificationMessage(
            type=NotificationType.CUSTOM,
            title="Test",
            body="Body",
            metadata={"webhook_url": "https://example.com/hook"},
        )
        with patch.object(p._session, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.ok = True
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            status = p.send(msg)
            assert status == DeliveryStatus.DELIVERED

    def test_send_with_url_fails(self):
        p = WebhookProvider(IntegrationsConfig())
        msg = NotificationMessage(
            type=NotificationType.CUSTOM,
            title="Test",
            body="Body",
            metadata={"webhook_url": "https://example.com/hook"},
        )
        with patch.object(p._session, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.ok = False
            mock_response.status_code = 500
            mock_response.text = "Server Error"
            mock_post.return_value = mock_response
            status = p.send(msg)
            assert status == DeliveryStatus.FAILED

    def test_send_request_exception(self):
        p = WebhookProvider(IntegrationsConfig())
        msg = NotificationMessage(
            type=NotificationType.CUSTOM,
            title="Test",
            body="Body",
            metadata={"webhook_url": "https://example.com/hook"},
        )
        with patch.object(p._session, "post", side_effect=requests.RequestException("Connection error")):
            status = p.send(msg)
            assert status == DeliveryStatus.FAILED

    def test_hmac_signing(self):
        cfg = IntegrationsConfig()
        cfg.webhook.hmac_enabled = True
        cfg.webhook.hmac_secret = "test-secret"
        p = WebhookProvider(cfg)
        msg = NotificationMessage(
            type=NotificationType.CUSTOM,
            title="Test",
            body="Body",
            metadata={"webhook_url": "https://example.com/hook"},
        )
        with patch.object(p._session, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.ok = True
            mock_post.return_value = mock_response
            status = p.send(msg)
            assert status == DeliveryStatus.DELIVERED
            call_kwargs = mock_post.call_args[1]
            assert "X-Signature-256" in call_kwargs["headers"]

    def test_health(self):
        p = WebhookProvider(IntegrationsConfig())
        h = p.health()
        assert h.status == ProviderStatus.HEALTHY

    def test_metadata(self):
        p = WebhookProvider(IntegrationsConfig())
        m = p.metadata()
        assert m.channel == DeliveryChannel.WEBHOOK
        assert m.supports_templates is True

    def test_shutdown(self):
        p = WebhookProvider(IntegrationsConfig())
        p.shutdown()


class TestSlackProvider:
    def test_initialize(self):
        p = SlackProvider(IntegrationsConfig())
        p.initialize()

    def test_validate_credentials_no_url(self):
        p = SlackProvider(IntegrationsConfig())
        assert p.validate_credentials() is False

    def test_validate_credentials_valid(self):
        cfg = IntegrationsConfig()
        cfg.slack.default_webhook_url = "https://hooks.slack.com/services/test"
        p = SlackProvider(cfg)
        assert p.validate_credentials() is True

    def test_send_no_url(self):
        p = SlackProvider(IntegrationsConfig())
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="Test", body="Body")
        status = p.send(msg)
        assert status == DeliveryStatus.FAILED

    def test_send_success(self):
        cfg = IntegrationsConfig()
        cfg.slack.default_webhook_url = "https://hooks.slack.com/services/test"
        p = SlackProvider(cfg)
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="Test", body="Body")
        with patch.object(p._session, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.ok = True
            mock_post.return_value = mock_response
            status = p.send(msg)
            assert status == DeliveryStatus.DELIVERED

    def test_send_request_exception(self):
        cfg = IntegrationsConfig()
        cfg.slack.default_webhook_url = "https://hooks.slack.com/services/test"
        p = SlackProvider(cfg)
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="Test", body="Body")
        with patch.object(p._session, "post", side_effect=requests.RequestException("fail")):
            status = p.send(msg)
            assert status == DeliveryStatus.FAILED

    def test_health_configured(self):
        cfg = IntegrationsConfig()
        cfg.slack.default_webhook_url = "https://hooks.slack.com/services/test"
        p = SlackProvider(cfg)
        h = p.health()
        assert h.status == ProviderStatus.HEALTHY

    def test_health_not_configured(self):
        p = SlackProvider(IntegrationsConfig())
        h = p.health()
        assert h.status == ProviderStatus.UNHEALTHY

    def test_metadata(self):
        p = SlackProvider(IntegrationsConfig())
        m = p.metadata()
        assert m.channel == DeliveryChannel.SLACK

    def test_shutdown(self):
        p = SlackProvider(IntegrationsConfig())
        p.shutdown()


class TestDiscordProvider:
    def test_initialize(self):
        p = DiscordProvider(IntegrationsConfig())
        p.initialize()

    def test_validate_credentials_no_url(self):
        p = DiscordProvider(IntegrationsConfig())
        assert p.validate_credentials() is False

    def test_send_no_url(self):
        p = DiscordProvider(IntegrationsConfig())
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="Test", body="Body")
        status = p.send(msg)
        assert status == DeliveryStatus.FAILED

    def test_send_success(self):
        cfg = IntegrationsConfig()
        cfg.discord.default_webhook_url = "https://discord.com/api/webhooks/test"
        p = DiscordProvider(cfg)
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="Test", body="Body")
        with patch.object(p._session, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.ok = True
            mock_post.return_value = mock_response
            status = p.send(msg)
            assert status == DeliveryStatus.DELIVERED

    def test_health(self):
        p = DiscordProvider(IntegrationsConfig())
        h = p.health()
        assert h.status == ProviderStatus.UNHEALTHY

    def test_metadata(self):
        p = DiscordProvider(IntegrationsConfig())
        m = p.metadata()
        assert m.channel == DeliveryChannel.DISCORD

    def test_shutdown(self):
        p = DiscordProvider(IntegrationsConfig())
        p.shutdown()


class TestTeamsProvider:
    def test_initialize(self):
        p = TeamsProvider(IntegrationsConfig())
        p.initialize()

    def test_validate_credentials_no_url(self):
        p = TeamsProvider(IntegrationsConfig())
        assert p.validate_credentials() is False

    def test_send_no_url(self):
        p = TeamsProvider(IntegrationsConfig())
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="Test", body="Body")
        status = p.send(msg)
        assert status == DeliveryStatus.FAILED

    def test_send_success(self):
        cfg = IntegrationsConfig()
        cfg.teams.default_webhook_url = "https://outlook.office.com/webhook/test"
        p = TeamsProvider(cfg)
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="Test", body="Body")
        with patch.object(p._session, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.ok = True
            mock_post.return_value = mock_response
            status = p.send(msg)
            assert status == DeliveryStatus.DELIVERED

    def test_health(self):
        p = TeamsProvider(IntegrationsConfig())
        h = p.health()
        assert h.status == ProviderStatus.UNHEALTHY

    def test_metadata(self):
        p = TeamsProvider(IntegrationsConfig())
        m = p.metadata()
        assert m.channel == DeliveryChannel.TEAMS

    def test_shutdown(self):
        p = TeamsProvider(IntegrationsConfig())
        p.shutdown()


# ── EmailSender Tests ──


class TestEmailSender:
    def test_build_message_plain(self):
        sender = EmailSender(IntegrationsConfig())
        msg = EmailMessage(to=["user@test.com"], subject="Test", body="Hello")
        mime = sender._build_message(msg)
        assert mime["Subject"] == "Test"
        assert mime["To"] == "user@test.com"
        assert mime["From"] == "noreply@aijobagent.com"

    def test_build_message_with_html(self):
        sender = EmailSender(IntegrationsConfig())
        msg = EmailMessage(to=["user@test.com"], subject="Test", body="Hello", html_body="<p>Hello</p>")
        mime = sender._build_message(msg)
        assert mime["Subject"] == "Test"

    def test_build_message_with_priority(self):
        sender = EmailSender(IntegrationsConfig())
        msg = EmailMessage(to=["user@test.com"], subject="Test", body="Hello", priority=NotificationPriority.HIGH)
        mime = sender._build_message(msg)
        assert mime["X-Priority"] == "2 (High)"

    def test_build_message_with_cc(self):
        sender = EmailSender(IntegrationsConfig())
        msg = EmailMessage(to=["user@test.com"], subject="Test", body="Hello", cc=["cc@test.com"])
        mime = sender._build_message(msg)
        assert mime["Cc"] == "cc@test.com"

    def test_build_message_with_reply_to(self):
        sender = EmailSender(IntegrationsConfig())
        msg = EmailMessage(to=["user@test.com"], subject="Test", body="Hello", reply_to="reply@test.com")
        mime = sender._build_message(msg)
        assert mime["Reply-To"] == "reply@test.com"

    def test_validate_credentials(self):
        sender = EmailSender(IntegrationsConfig())
        result = sender.validate_credentials()
        assert result is False

    def test_send_fails_no_server(self):
        sender = EmailSender(IntegrationsConfig())
        msg = EmailMessage(to=["user@test.com"], subject="Test", body="Hello")
        with pytest.raises(DeliveryError):
            sender.send(msg)


# ── Provider Interface Tests ──


class TestNotificationProviderInterface:
    def test_mock_provider_send(self):
        p = MockNotificationProvider(IntegrationsConfig())
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="T", body="B")
        assert p.send(msg) == DeliveryStatus.DELIVERED

    def test_mock_provider_health(self):
        p = MockNotificationProvider(IntegrationsConfig())
        assert p.health().status == ProviderStatus.HEALTHY

    def test_failing_provider_send(self):
        p = FailingMockNotificationProvider(IntegrationsConfig())
        msg = NotificationMessage(type=NotificationType.CUSTOM, title="T", body="B")
        assert p.send(msg) == DeliveryStatus.FAILED

    def test_provider_is_abstract(self):
        with pytest.raises(TypeError):
            NotificationProvider()  # type: ignore

    def test_base_provider_abstract(self):
        with pytest.raises(TypeError):
            BaseNotificationProvider(IntegrationsConfig())  # type: ignore

    def test_shutdown_default(self):
        p = MockNotificationProvider(IntegrationsConfig())
        p.shutdown()


# ── DI Tests ──


class TestIntegrationDependencies:
    def test_get_provider_registry_is_singleton(self):
        reset_integration_service()
        r1 = get_provider_registry()
        r2 = get_provider_registry()
        assert r1 is r2

    def test_get_integrations_config(self):
        c = get_integrations_config()
        assert isinstance(c, IntegrationsConfig)

    def test_get_integration_service(self):
        reset_integration_service()
        svc = get_integration_service()
        assert isinstance(svc, IntegrationService)

    def test_get_integration_service_is_singleton(self):
        reset_integration_service()
        s1 = get_integration_service()
        s2 = get_integration_service()
        assert s1 is s2
