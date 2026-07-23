from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.ats.config import (
    AshbyATSConfig,
    ATSConfig,
    BambooHRATSConfig,
    GreenhouseATSConfig,
    LeverATSConfig,
    RecruiteeATSConfig,
    SmartRecruitersATSConfig,
    WorkdayATSConfig,
)
from app.ats.dependencies import get_ats_service, reset_ats_service
from app.ats.exceptions import (
    ATSApplicationError,
    ATSConfigError,
    ATSDetectionError,
    ATSError,
    ATSJobNotFoundError,
    ATSLoginError,
    ATSNavigationError,
    ATSNotSupportedError,
    ATSProviderAuthError,
    ATSProviderDuplicateError,
    ATSProviderError,
    ATSProviderNotFoundError,
    ATSProviderRateLimitError,
    ATSProviderRegistrationError,
    ATSProviderStateError,
    ATSProviderTimeoutError,
    ATSProviderUnavailableError,
    ATSValidationError,
)
from app.ats.factory import ATSProviderFactory
from app.ats.providers.ashby import AshbyATSProvider
from app.ats.providers.bamboohr import BambooHRATSProvider
from app.ats.providers.base import BaseATSProvider
from app.ats.providers.greenhouse import GreenhouseATSProvider
from app.ats.providers.lever import LeverATSProvider
from app.ats.providers.recruitee import RecruiteeATSProvider
from app.ats.providers.smartrecruiters import SmartRecruitersATSProvider
from app.ats.providers.workday import WorkdayATSProvider
from app.ats.registry import ATSProviderRegistry
from app.ats.schemas import (
    ATSApplicationRequest,
    ATSApplicationResult,
    ATSDetectionResult,
    ATSJobInfo,
    ATSJobSearchRequest,
    ATSLoginRequest,
    ATSLoginResult,
    ATSNavigationRequest,
    ATSProviderCapability,
    ATSProviderConfig,
    ATSProviderMetadata,
    ATSProviderState,
    ATSValidationResult,
)
from app.ats.service import ATSService
from app.browser.service import BrowserService

# ═══════════════════════════════════════════════════════════════════════
#  Fixtures
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def mock_page():
    page = MagicMock()
    page.url = "https://example.com"
    page.title.return_value = "Example"
    page.content.return_value = "<html></html>"
    page.query_selector.return_value = None
    page.query_selector_all.return_value = []
    return page


@pytest.fixture
def mock_browser():
    browser = MagicMock(spec=BrowserService)
    browser.create_browser.return_value = {"id": "b1"}
    browser.create_context.return_value = {"id": "c1"}
    browser.create_session.return_value = {"id": "s1"}
    nav_result = MagicMock()
    nav_result.success = True
    nav_result.url = "https://example.com"
    nav_result.title = "Example"
    nav_result.duration_ms = 100.0
    nav_result.error = None
    browser.navigate.return_value = nav_result
    browser.safe_click.return_value = None
    browser.safe_fill.return_value = None
    browser.wait_for_network_idle.return_value = None
    browser.wait_for_selector.return_value = MagicMock()
    browser.get_text.return_value = ""
    browser.is_visible.return_value = True
    browser.upload_file.return_value = None
    browser.take_screenshot.return_value = "/screenshots/test.png"
    browser.take_failure_screenshot.return_value = "/screenshots/fail.png"
    return browser


@pytest.fixture
def ats_config():
    return ATSConfig()


@pytest.fixture
def registry():
    return ATSProviderRegistry()


@pytest.fixture
def greenhouse_provider(mock_browser):
    return GreenhouseATSProvider(mock_browser)


@pytest.fixture
def lever_provider(mock_browser):
    return LeverATSProvider(mock_browser)


@pytest.fixture
def ashby_provider(mock_browser):
    return AshbyATSProvider(mock_browser)


@pytest.fixture
def workday_provider(mock_browser):
    return WorkdayATSProvider(mock_browser)


@pytest.fixture
def smartrecruiters_provider(mock_browser):
    return SmartRecruitersATSProvider(mock_browser)


@pytest.fixture
def bamboohr_provider(mock_browser):
    return BambooHRATSProvider(mock_browser)


@pytest.fixture
def recruitee_provider(mock_browser):
    return RecruiteeATSProvider(mock_browser)


@pytest.fixture
def registered_registry(
    greenhouse_provider,
    lever_provider,
    ashby_provider,
    workday_provider,
    smartrecruiters_provider,
    bamboohr_provider,
    recruitee_provider,
):
    r = ATSProviderRegistry()
    r.register(greenhouse_provider)
    r.register(lever_provider)
    r.register(ashby_provider)
    r.register(workday_provider)
    r.register(smartrecruiters_provider)
    r.register(bamboohr_provider)
    r.register(recruitee_provider)
    return r


@pytest.fixture
def factory(registered_registry, ats_config, mock_browser):
    return ATSProviderFactory(registered_registry, ats_config, mock_browser)


@pytest.fixture
def ats_service(registered_registry, factory, ats_config, mock_browser):
    return ATSService(registered_registry, factory, ats_config, mock_browser)


# ═══════════════════════════════════════════════════════════════════════
#  Schemas
# ═══════════════════════════════════════════════════════════════════════


class TestATSProviderState:
    def test_values(self):
        assert ATSProviderState.UNKNOWN.value == "unknown"
        assert ATSProviderState.DETECTED.value == "detected"
        assert ATSProviderState.CONNECTED.value == "connected"
        assert ATSProviderState.LOGGED_IN.value == "logged_in"
        assert ATSProviderState.NAVIGATING.value == "navigating"
        assert ATSProviderState.ON_JOB.value == "on_job"
        assert ATSProviderState.APPLYING.value == "applying"
        assert ATSProviderState.SUBMITTED.value == "submitted"
        assert ATSProviderState.ERROR.value == "error"
        assert ATSProviderState.CLOSED.value == "closed"


class TestATSProviderCapability:
    def test_values(self):
        assert ATSProviderCapability.JOB_SEARCH.value == "job_search"
        assert ATSProviderCapability.JOB_DETAILS.value == "job_details"
        assert ATSProviderCapability.APPLY.value == "apply"
        assert ATSProviderCapability.UPLOAD_RESUME.value == "upload_resume"
        assert ATSProviderCapability.UPLOAD_COVER_LETTER.value == "upload_cover_letter"
        assert ATSProviderCapability.AUTO_FILL.value == "auto_fill"
        assert ATSProviderCapability.LOGIN.value == "login"
        assert ATSProviderCapability.LOGOUT.value == "logout"
        assert ATSProviderCapability.SCREENSHOT.value == "screenshot"
        assert ATSProviderCapability.VALIDATE.value == "validate"
        assert ATSProviderCapability.DETECT.value == "detect"


class TestATSProviderMetadata:
    def test_defaults(self):
        m = ATSProviderMetadata(name="test", display_name="Test")
        assert m.version == "0.1.0"
        assert m.capabilities == []
        assert m.url_patterns == []
        assert m.requires_auth is False
        assert m.requires_login is False
        assert m.max_file_size_mb == 10
        assert ".pdf" in m.allowed_file_types

    def test_custom(self):
        m = ATSProviderMetadata(
            name="gh",
            display_name="Greenhouse",
            version="2.0.0",
            capabilities=[ATSProviderCapability.APPLY],
            url_patterns=["greenhouse"],
            requires_login=True,
        )
        assert m.name == "gh"
        assert m.capabilities == [ATSProviderCapability.APPLY]


class TestATSDetectionResult:
    def test_defaults(self):
        r = ATSDetectionResult(
            provider_name="gh", provider_display_name="Greenhouse", url="https://boards.greenhouse.io"
        )
        assert r.confidence == 1.0
        assert r.matched_pattern is None


class TestATSLoginRequest:
    def test_defaults(self):
        r = ATSLoginRequest()
        assert r.email is None
        assert r.password is None
        assert r.credentials == {}


class TestATSLoginResult:
    def test_defaults(self):
        r = ATSLoginResult(success=True)
        assert r.requires_mfa is False


class TestATSJobSearchRequest:
    def test_defaults(self):
        r = ATSJobSearchRequest()
        assert r.query is None
        assert r.offset == 0
        assert r.limit == 20


class TestATSJobInfo:
    def test_defaults(self):
        j = ATSJobInfo(provider_job_id="123", title="Engineer", url="https://example.com/job")
        assert j.location is None
        assert j.department is None


class TestATSApplicationRequest:
    def test_defaults(self):
        r = ATSApplicationRequest(job_id="123", job_url="https://example.com/apply")
        assert r.resume_path is None
        assert r.fields == {}


class TestATSApplicationResult:
    def test_defaults(self):
        r = ATSApplicationResult(success=True)
        assert r.application_id is None
        assert r.errors == []


class TestATSValidationResult:
    def test_defaults(self):
        r = ATSValidationResult(valid=True)
        assert r.errors == []
        assert r.warnings == []


class TestATSProviderConfig:
    def test_defaults(self):
        c = ATSProviderConfig(name="greenhouse")
        assert c.enabled is True
        assert c.headless is True
        assert c.retry_attempts == 3


# ═══════════════════════════════════════════════════════════════════════
#  Config
# ═══════════════════════════════════════════════════════════════════════


class TestATSConfig:
    def test_defaults(self):
        c = ATSConfig()
        assert c.default_headless is True
        assert c.default_timeout_ms == 60000.0
        assert c.screenshot_on_error is True

    def test_sub_configs(self):
        c = ATSConfig()
        assert isinstance(c.greenhouse, GreenhouseATSConfig)
        assert isinstance(c.lever, LeverATSConfig)
        assert isinstance(c.ashby, AshbyATSConfig)
        assert isinstance(c.workday, WorkdayATSConfig)
        assert isinstance(c.smartrecruiters, SmartRecruitersATSConfig)
        assert isinstance(c.bamboohr, BambooHRATSConfig)
        assert isinstance(c.recruitee, RecruiteeATSConfig)

    def test_greenhouse_config(self):
        c = GreenhouseATSConfig()
        assert c.base_url == "https://boards.greenhouse.io"
        assert c.login_url == "https://app.greenhouse.io/users/sign_in"

    def test_workday_config(self):
        c = WorkdayATSConfig()
        assert c.base_url == "https://www.myworkdayjobs.com"

    def test_bamboohr_config(self):
        c = BambooHRATSConfig()
        assert "bamboohr.com" in c.login_url

    def test_recruitee_config(self):
        c = RecruiteeATSConfig()
        assert "recruitee.com" in c.base_url
        assert "{company}" in c.base_url


# ═══════════════════════════════════════════════════════════════════════
#  Exceptions
# ═══════════════════════════════════════════════════════════════════════


class TestATSExceptions:
    def test_ats_error(self):
        e = ATSError(message="ats error")
        assert e.code == "ATS_ERROR"
        assert e.status_code == 502

    def test_provider_not_found(self):
        e = ATSProviderNotFoundError(message="not found")
        assert e.code == "ATS_PROVIDER_NOT_FOUND"
        assert e.status_code == 404

    def test_provider_unavailable(self):
        e = ATSProviderUnavailableError(message="unavailable")
        assert e.code == "ATS_PROVIDER_UNAVAILABLE"

    def test_not_supported(self):
        e = ATSNotSupportedError(message="not supported")
        assert e.code == "ATS_NOT_SUPPORTED"
        assert e.status_code == 400

    def test_login_error(self):
        e = ATSLoginError(message="login failed")
        assert e.code == "ATS_LOGIN_ERROR"
        assert e.status_code == 401

    def test_navigation_error(self):
        e = ATSNavigationError(message="nav failed")
        assert e.code == "ATS_NAVIGATION_ERROR"
        assert e.status_code == 400

    def test_job_not_found(self):
        e = ATSJobNotFoundError(message="job not found")
        assert e.code == "ATS_JOB_NOT_FOUND"
        assert e.status_code == 404

    def test_application_error(self):
        e = ATSApplicationError(message="app failed")
        assert e.code == "ATS_APPLICATION_ERROR"
        assert e.status_code == 400

    def test_validation_error(self):
        e = ATSValidationError(message="validation failed")
        assert e.code == "ATS_VALIDATION_ERROR"
        assert e.status_code == 400

    def test_detection_error(self):
        e = ATSDetectionError(message="detection failed")
        assert e.code == "ATS_DETECTION_ERROR"
        assert e.status_code == 400

    def test_config_error(self):
        e = ATSConfigError(message="config error")
        assert e.code == "ATS_CONFIG_ERROR"
        assert e.status_code == 500

    def test_provider_error(self):
        e = ATSProviderError(message="provider error")
        assert e.code == "ATS_PROVIDER_ERROR"
        assert e.status_code == 502

    def test_provider_timeout(self):
        e = ATSProviderTimeoutError(message="timeout")
        assert e.code == "ATS_PROVIDER_TIMEOUT"

    def test_provider_auth(self):
        e = ATSProviderAuthError(message="auth error")
        assert e.code == "ATS_PROVIDER_AUTH_ERROR"
        assert e.status_code == 401

    def test_provider_rate_limit(self):
        e = ATSProviderRateLimitError(message="rate limit")
        assert e.code == "ATS_PROVIDER_RATE_LIMIT"
        assert e.status_code == 429

    def test_provider_state_error(self):
        e = ATSProviderStateError(message="state error")
        assert e.code == "ATS_PROVIDER_STATE_ERROR"

    def test_provider_registration_error(self):
        e = ATSProviderRegistrationError(message="reg error")
        assert e.code == "ATS_PROVIDER_REGISTRATION_ERROR"
        assert e.status_code == 500

    def test_provider_duplicate(self):
        e = ATSProviderDuplicateError(message="dup")
        assert e.code == "ATS_PROVIDER_DUPLICATE"
        assert e.status_code == 409


# ═══════════════════════════════════════════════════════════════════════
#  Registry
# ═══════════════════════════════════════════════════════════════════════


class TestATSProviderRegistry:
    def test_register_and_resolve(self, greenhouse_provider):
        r = ATSProviderRegistry()
        r.register(greenhouse_provider)
        assert r.is_registered("greenhouse")
        assert r.resolve("greenhouse") is greenhouse_provider

    def test_register_duplicate_raises(self, greenhouse_provider):
        r = ATSProviderRegistry()
        r.register(greenhouse_provider)
        with pytest.raises(ATSProviderDuplicateError):
            r.register(greenhouse_provider)

    def test_register_or_replace(self, greenhouse_provider, mock_browser):
        r = ATSProviderRegistry()
        r.register(greenhouse_provider)
        replacement = GreenhouseATSProvider(mock_browser)
        r.register_or_replace(replacement)
        assert r.count() == 1

    def test_unregister(self, greenhouse_provider):
        r = ATSProviderRegistry()
        r.register(greenhouse_provider)
        r.unregister("greenhouse")
        assert not r.is_registered("greenhouse")

    def test_unregister_missing_raises(self):
        r = ATSProviderRegistry()
        with pytest.raises(ATSProviderNotFoundError):
            r.unregister("nonexistent")

    def test_resolve_missing_raises(self):
        r = ATSProviderRegistry()
        with pytest.raises(ATSProviderNotFoundError):
            r.resolve("nonexistent")

    def test_detect(self, registered_registry):
        provider = registered_registry.detect("https://boards.greenhouse.io/example/jobs/123")
        assert provider is not None
        assert provider.name == "greenhouse"

    def test_detect_returns_none(self, registered_registry):
        provider = registered_registry.detect("https://unknown-ats.com/jobs")
        assert provider is None

    def test_detect_result(self, registered_registry):
        result = registered_registry.detect_result("https://jobs.lever.co/company/role")
        assert result is not None
        assert result.provider_name == "lever"
        assert result.provider_display_name == "Lever"

    def test_detect_result_returns_none(self, registered_registry):
        result = registered_registry.detect_result("https://unknown.com")
        assert result is None

    def test_list_providers(self, registered_registry):
        names = registered_registry.list_providers()
        assert "greenhouse" in names
        assert "lever" in names
        assert "ashby" in names
        assert "workday" in names
        assert "smartrecruiters" in names
        assert "bamboohr" in names
        assert "recruitee" in names

    def test_list_details(self, registered_registry):
        details = registered_registry.list_details()
        names = [d["name"] for d in details]
        assert "greenhouse" in names
        assert all("capabilities" in d for d in details)

    def test_clear(self, greenhouse_provider):
        r = ATSProviderRegistry()
        r.register(greenhouse_provider)
        r.clear()
        assert r.count() == 0


# ═══════════════════════════════════════════════════════════════════════
#  Base Provider
# ═══════════════════════════════════════════════════════════════════════


class TestBaseATSProvider:
    def test_supports_with_patterns(self, mock_browser):
        class TestProvider(BaseATSProvider):
            name = "test"
            display_name = "Test"
            url_patterns = [r"test\.example\.com"]

        p = TestProvider(mock_browser)
        assert p.supports("https://test.example.com/jobs")
        assert not p.supports("https://other.com")

    def test_detect_matches(self, mock_browser):
        class TestProvider(BaseATSProvider):
            name = "test"
            display_name = "Test"
            url_patterns = [r"test\.example\.com"]

        p = TestProvider(mock_browser)
        result = p.detect("https://test.example.com/jobs")
        assert result is not None
        assert result.provider_name == "test"
        assert result.confidence == 0.95

    def test_detect_no_match(self, mock_browser):
        class TestProvider(BaseATSProvider):
            name = "test"
            display_name = "Test"
            url_patterns = [r"test\.example\.com"]

        p = TestProvider(mock_browser)
        result = p.detect("https://other.com")
        assert result is None

    def test_login_not_required(self, mock_browser, mock_page):
        class TestProvider(BaseATSProvider):
            name = "test"
            display_name = "Test"
            requires_login = False

        p = TestProvider(mock_browser)
        result = p.login(mock_page, ATSLoginRequest())
        assert result.success

    def test_login_required_not_impl(self, mock_browser, mock_page):
        class TestProvider(BaseATSProvider):
            name = "test"
            display_name = "Test"
            requires_login = True

        p = TestProvider(mock_browser)
        with pytest.raises(ATSNotSupportedError):
            p.login(mock_page, ATSLoginRequest())

    def test_navigate_success(self, mock_browser, mock_page):
        class TestProvider(BaseATSProvider):
            name = "test"
            display_name = "Test"

        p = TestProvider(mock_browser)
        result = p.navigate(mock_page, ATSNavigationRequest(url="https://example.com"))
        assert result.success

    def test_find_job_not_impl(self, mock_browser, mock_page):
        class TestProvider(BaseATSProvider):
            name = "test"
            display_name = "Test"

        p = TestProvider(mock_browser)
        with pytest.raises(ATSNotSupportedError):
            p.find_job(mock_page, ATSJobSearchRequest())

    def test_open_application_not_impl(self, mock_browser, mock_page):
        class TestProvider(BaseATSProvider):
            name = "test"
            display_name = "Test"

        p = TestProvider(mock_browser)
        with pytest.raises(ATSNotSupportedError):
            p.open_application(mock_page, ATSApplicationRequest(job_id="1", job_url="https://example.com"))

    def test_validate_default(self, mock_browser, mock_page):
        class TestProvider(BaseATSProvider):
            name = "test"
            display_name = "Test"

        p = TestProvider(mock_browser)
        result = p.validate(mock_page)
        assert result.valid
        assert result.provider_name == "test"

    def test_capabilities(self, mock_browser):
        class TestProvider(BaseATSProvider):
            name = "test"
            display_name = "Test"
            _capabilities = [ATSProviderCapability.DETECT, ATSProviderCapability.VALIDATE]

        p = TestProvider(mock_browser)
        caps = p.capabilities()
        assert ATSProviderCapability.DETECT in caps
        assert ATSProviderCapability.VALIDATE in caps

    def test_metadata(self, mock_browser):
        class TestProvider(BaseATSProvider):
            name = "test"
            display_name = "Test Provider"
            description = "A test provider"
            version = "2.0.0"
            homepage_url = "https://test.com"
            _capabilities = [ATSProviderCapability.DETECT]
            url_patterns = [r"test\.com"]

        p = TestProvider(mock_browser)
        m = p.metadata()
        assert m.name == "test"
        assert m.display_name == "Test Provider"
        assert m.homepage_url == "https://test.com"
        assert m.capabilities == [ATSProviderCapability.DETECT]

    def test_click_and_wait(self, mock_browser, mock_page):
        p = BaseATSProvider.__new__(BaseATSProvider)
        p.browser = mock_browser
        p._click_and_wait(mock_page, "#button")
        mock_browser.safe_click.assert_called_once_with(mock_page, "#button", None)

    def test_fill_and_wait(self, mock_browser, mock_page):
        p = BaseATSProvider.__new__(BaseATSProvider)
        p.browser = mock_browser
        p._fill_and_wait(mock_page, "#input", "value")
        mock_browser.safe_fill.assert_called_once_with(mock_page, "#input", "value", None)

    def test_wait_and_get_text(self, mock_browser, mock_page):
        mock_browser.get_text.return_value = "some text"
        p = BaseATSProvider.__new__(BaseATSProvider)
        p.browser = mock_browser
        result = p._wait_and_get_text(mock_page, "#text-el")
        assert result == "some text"

    def test_is_element_present(self, mock_browser, mock_page):
        mock_browser.is_visible.return_value = True
        p = BaseATSProvider.__new__(BaseATSProvider)
        p.browser = mock_browser
        assert p._is_element_present(mock_page, "#el")

    def test_take_screenshot(self, mock_browser, mock_page):
        mock_browser.take_screenshot.return_value = "/screenshots/test.png"
        p = BaseATSProvider.__new__(BaseATSProvider)
        p.browser = mock_browser
        result = p._take_screenshot(mock_page, "test")
        assert result == "/screenshots/test.png"


# ═══════════════════════════════════════════════════════════════════════
#  Greenhouse Provider
# ═══════════════════════════════════════════════════════════════════════


class TestGreenhouseATSProvider:
    def test_supports(self, greenhouse_provider):
        assert greenhouse_provider.supports("https://boards.greenhouse.io/example/jobs/123")
        assert not greenhouse_provider.supports("https://jobs.lever.co/example")

    def test_detect(self, greenhouse_provider):
        result = greenhouse_provider.detect("https://boards.greenhouse.io/example")
        assert result is not None
        assert result.provider_name == "greenhouse"

    def test_capabilities(self, greenhouse_provider):
        caps = greenhouse_provider.capabilities()
        assert ATSProviderCapability.JOB_SEARCH in caps
        assert ATSProviderCapability.APPLY in caps
        assert ATSProviderCapability.UPLOAD_RESUME in caps

    def test_metadata(self, greenhouse_provider):
        m = greenhouse_provider.metadata()
        assert m.name == "greenhouse"
        assert m.display_name == "Greenhouse"
        assert ATSProviderCapability.APPLY in m.capabilities

    def test_login_success(self, greenhouse_provider, mock_page):
        greenhouse_provider.browser = MagicMock()
        result = greenhouse_provider.login(mock_page, ATSLoginRequest(email="test@test.com", password="pass"))
        assert result.success

    def test_login_missing_credentials(self, greenhouse_provider, mock_page):
        with pytest.raises(ATSLoginError):
            greenhouse_provider.login(mock_page, ATSLoginRequest())

    def test_login_failure_raises(self, greenhouse_provider, mock_page):
        greenhouse_provider.browser = MagicMock()
        greenhouse_provider.browser.safe_click.side_effect = Exception("click failed")
        with pytest.raises(ATSLoginError):
            greenhouse_provider.login(mock_page, ATSLoginRequest(email="test@test.com", password="pass"))

    def test_validate_greenhouse_url(self, greenhouse_provider, mock_page):
        mock_page.url = "https://boards.greenhouse.io/example"
        result = greenhouse_provider.validate(mock_page)
        assert result.valid

    def test_validate_non_greenhouse_url(self, greenhouse_provider, mock_page):
        mock_page.url = "https://example.com"
        result = greenhouse_provider.validate(mock_page)
        assert not result.valid

    def test_open_application_success(self, greenhouse_provider, mock_page):
        greenhouse_provider.browser = MagicMock()
        request = ATSApplicationRequest(job_id="123", job_url="https://boards.greenhouse.io/example/jobs/123")
        result = greenhouse_provider.open_application(mock_page, request)
        assert result.success

    def test_open_application_failure(self, greenhouse_provider, mock_page):
        greenhouse_provider.browser = MagicMock()
        greenhouse_provider.browser.safe_click.side_effect = Exception("click failed")
        request = ATSApplicationRequest(job_id="123", job_url="https://boards.greenhouse.io/example/jobs/123")
        result = greenhouse_provider.open_application(mock_page, request)
        assert not result.success

    def test_extract_board_token(self, greenhouse_provider):
        token = greenhouse_provider._extract_board_token("https://boards.greenhouse.io/acme")
        assert token == "acme"

    def test_extract_board_token_default(self, greenhouse_provider):
        token = greenhouse_provider._extract_board_token("https://example.com")
        assert token == "example"


# ═══════════════════════════════════════════════════════════════════════
#  Lever Provider
# ═══════════════════════════════════════════════════════════════════════


class TestLeverATSProvider:
    def test_supports(self, lever_provider):
        assert lever_provider.supports("https://jobs.lever.co/company/role")
        assert not lever_provider.supports("https://boards.greenhouse.io/example")

    def test_detect(self, lever_provider):
        result = lever_provider.detect("https://jobs.lever.co/company")
        assert result is not None
        assert result.provider_name == "lever"

    def test_capabilities(self, lever_provider):
        caps = lever_provider.capabilities()
        assert ATSProviderCapability.JOB_SEARCH in caps
        assert ATSProviderCapability.APPLY in caps

    def test_login_success(self, lever_provider, mock_page):
        lever_provider.browser = MagicMock()
        result = lever_provider.login(mock_page, ATSLoginRequest(email="test@test.com", password="pass"))
        assert result.success

    def test_login_missing_credentials(self, lever_provider, mock_page):
        with pytest.raises(ATSLoginError):
            lever_provider.login(mock_page, ATSLoginRequest())

    def test_validate_lever_url(self, lever_provider, mock_page):
        mock_page.url = "https://jobs.lever.co/company"
        result = lever_provider.validate(mock_page)
        assert result.valid

    def test_validate_non_lever_url(self, lever_provider, mock_page):
        mock_page.url = "https://example.com"
        result = lever_provider.validate(mock_page)
        assert not result.valid

    def test_open_application_success(self, lever_provider, mock_page):
        lever_provider.browser = MagicMock()
        request = ATSApplicationRequest(job_id="123", job_url="https://jobs.lever.co/company/role")
        result = lever_provider.open_application(mock_page, request)
        assert result.success

    def test_extract_job_id(self, lever_provider):
        job_id = lever_provider._extract_job_id("https://jobs.lever.co/company/abc123")
        assert job_id == "abc123"


# ═══════════════════════════════════════════════════════════════════════
#  Ashby Provider
# ═══════════════════════════════════════════════════════════════════════


class TestAshbyATSProvider:
    def test_supports(self, ashby_provider):
        assert ashby_provider.supports("https://jobs.ashbyhq.com/company")
        assert not ashby_provider.supports("https://example.com")

    def test_detect(self, ashby_provider):
        result = ashby_provider.detect("https://jobs.ashbyhq.com/company/jobs/123")
        assert result is not None
        assert result.provider_name == "ashby"

    def test_capabilities(self, ashby_provider):
        caps = ashby_provider.capabilities()
        assert ATSProviderCapability.APPLY in caps
        assert ATSProviderCapability.UPLOAD_RESUME in caps

    def test_login(self, ashby_provider, mock_page):
        result = ashby_provider.login(mock_page, ATSLoginRequest())
        assert result.success

    def test_validate_ashby_url(self, ashby_provider, mock_page):
        mock_page.url = "https://jobs.ashbyhq.com/company"
        result = ashby_provider.validate(mock_page)
        assert result.valid

    def test_extract_job_id(self, ashby_provider):
        job_id = ashby_provider._extract_job_id("https://jobs.ashbyhq.com/jobs/abc123")
        assert job_id == "abc123"


# ═══════════════════════════════════════════════════════════════════════
#  Workday Provider
# ═══════════════════════════════════════════════════════════════════════


class TestWorkdayATSProvider:
    def test_supports(self, workday_provider):
        assert workday_provider.supports("https://myworkdayjobs.com/company")
        assert not workday_provider.supports("https://example.com")

    def test_detect(self, workday_provider):
        result = workday_provider.detect("https://myworkdayjobs.com/company/job/123")
        assert result is not None
        assert result.provider_name == "workday"

    def test_capabilities(self, workday_provider):
        caps = workday_provider.capabilities()
        assert ATSProviderCapability.JOB_SEARCH in caps
        assert ATSProviderCapability.APPLY in caps

    def test_login_missing_credentials(self, workday_provider, mock_page):
        with pytest.raises(ATSLoginError):
            workday_provider.login(mock_page, ATSLoginRequest())

    def test_validate_workday_url(self, workday_provider, mock_page):
        mock_page.url = "https://myworkdayjobs.com/company"
        result = workday_provider.validate(mock_page)
        assert result.valid

    def test_extract_job_id(self, workday_provider):
        job_id = workday_provider._extract_job_id("https://myworkdayjobs.com/company/job/123")
        assert job_id == "123"


# ═══════════════════════════════════════════════════════════════════════
#  SmartRecruiters Provider
# ═══════════════════════════════════════════════════════════════════════


class TestSmartRecruitersATSProvider:
    def test_supports(self, smartrecruiters_provider):
        assert smartrecruiters_provider.supports("https://jobs.smartrecruiters.com/company")
        assert not smartrecruiters_provider.supports("https://example.com")

    def test_detect(self, smartrecruiters_provider):
        result = smartrecruiters_provider.detect("https://jobs.smartrecruiters.com/company/12345")
        assert result is not None
        assert result.provider_name == "smartrecruiters"

    def test_capabilities(self, smartrecruiters_provider):
        caps = smartrecruiters_provider.capabilities()
        assert ATSProviderCapability.APPLY in caps
        assert ATSProviderCapability.UPLOAD_RESUME in caps

    def test_login(self, smartrecruiters_provider, mock_page):
        result = smartrecruiters_provider.login(mock_page, ATSLoginRequest())
        assert result.success

    def test_validate_sr_url(self, smartrecruiters_provider, mock_page):
        mock_page.url = "https://jobs.smartrecruiters.com/company"
        result = smartrecruiters_provider.validate(mock_page)
        assert result.valid

    def test_extract_job_id(self, smartrecruiters_provider):
        job_id = smartrecruiters_provider._extract_job_id("https://jobs.smartrecruiters.com/company/12345")
        assert job_id == "12345"


# ═══════════════════════════════════════════════════════════════════════
#  BambooHR Provider
# ═══════════════════════════════════════════════════════════════════════


class TestBambooHRATSProvider:
    def test_supports(self, bamboohr_provider):
        assert bamboohr_provider.supports("https://company.bamboohr.com")
        assert not bamboohr_provider.supports("https://example.com")

    def test_detect(self, bamboohr_provider):
        result = bamboohr_provider.detect("https://company.bamboohr.com/careers")
        assert result is not None
        assert result.provider_name == "bamboohr"

    def test_capabilities(self, bamboohr_provider):
        caps = bamboohr_provider.capabilities()
        assert ATSProviderCapability.LOGIN in caps
        assert ATSProviderCapability.APPLY in caps

    def test_login_missing_credentials(self, bamboohr_provider, mock_page):
        with pytest.raises(ATSLoginError):
            bamboohr_provider.login(mock_page, ATSLoginRequest())

    def test_login_missing_subdomain(self, bamboohr_provider, mock_page):
        mock_page.url = "https://example.com"
        with pytest.raises(ATSLoginError):
            bamboohr_provider.login(mock_page, ATSLoginRequest(email="test@test.com", password="pass"))

    def test_validate_bamboohr_url(self, bamboohr_provider, mock_page):
        mock_page.url = "https://company.bamboohr.com"
        result = bamboohr_provider.validate(mock_page)
        assert result.valid

    def test_requires_login(self, bamboohr_provider):
        assert bamboohr_provider.requires_login is True

    def test_extract_job_id(self, bamboohr_provider):
        job_id = bamboohr_provider._extract_job_id("https://company.bamboohr.com/careers/123")
        assert job_id == "123"


# ═══════════════════════════════════════════════════════════════════════
#  Recruitee Provider
# ═══════════════════════════════════════════════════════════════════════


class TestRecruiteeATSProvider:
    def test_supports(self, recruitee_provider):
        assert recruitee_provider.supports("https://company.recruitee.com")
        assert not recruitee_provider.supports("https://example.com")

    def test_detect(self, recruitee_provider):
        result = recruitee_provider.detect("https://company.recruitee.com/o/jobs/123")
        assert result is not None
        assert result.provider_name == "recruitee"

    def test_capabilities(self, recruitee_provider):
        caps = recruitee_provider.capabilities()
        assert ATSProviderCapability.APPLY in caps
        assert ATSProviderCapability.UPLOAD_RESUME in caps

    def test_login_missing_credentials(self, recruitee_provider, mock_page):
        with pytest.raises(ATSLoginError):
            recruitee_provider.login(mock_page, ATSLoginRequest())

    def test_validate_recruitee_url(self, recruitee_provider, mock_page):
        mock_page.url = "https://company.recruitee.com"
        result = recruitee_provider.validate(mock_page)
        assert result.valid

    def test_extract_job_id(self, recruitee_provider):
        job_id = recruitee_provider._extract_job_id("https://company.recruitee.com/o/senior-engineer")
        assert job_id == "senior-engineer"


# ═══════════════════════════════════════════════════════════════════════
#  Factory
# ═══════════════════════════════════════════════════════════════════════


class TestATSProviderFactory:
    def test_register_all(self, registry, ats_config, mock_browser):
        factory = ATSProviderFactory(registry, ats_config, mock_browser)
        factory.register_all()
        assert registry.count() == 7
        assert "greenhouse" in registry.list_providers()
        assert "lever" in registry.list_providers()
        assert "ashby" in registry.list_providers()
        assert "workday" in registry.list_providers()
        assert "smartrecruiters" in registry.list_providers()
        assert "bamboohr" in registry.list_providers()
        assert "recruitee" in registry.list_providers()

    def test_register_all_skips_existing(self, registry, ats_config, mock_browser):
        existing = GreenhouseATSProvider(mock_browser)
        registry.register(existing)
        factory = ATSProviderFactory(registry, ats_config, mock_browser)
        factory.register_all()
        assert registry.count() == 7
        assert registry.resolve("greenhouse") is existing

    def test_create_provider(self, ats_config, mock_browser):
        registry = ATSProviderRegistry()
        factory = ATSProviderFactory(registry, ats_config, mock_browser)
        gh = factory.create_provider("greenhouse")
        assert isinstance(gh, GreenhouseATSProvider)
        lv = factory.create_provider("lever")
        assert isinstance(lv, LeverATSProvider)

    def test_create_provider_unknown(self, ats_config, mock_browser):
        registry = ATSProviderRegistry()
        factory = ATSProviderFactory(registry, ats_config, mock_browser)
        with pytest.raises(ValueError):
            factory.create_provider("unknown")

    def test_detect_provider(self, registered_registry, ats_config, mock_browser):
        factory = ATSProviderFactory(registered_registry, ats_config, mock_browser)
        provider = factory.detect_provider("https://boards.greenhouse.io/example")
        assert provider is not None
        assert provider.name == "greenhouse"

    def test_detect_provider_returns_none(self, registered_registry, ats_config, mock_browser):
        factory = ATSProviderFactory(registered_registry, ats_config, mock_browser)
        provider = factory.detect_provider("https://unknown.com")
        assert provider is None


# ═══════════════════════════════════════════════════════════════════════
#  Service
# ═══════════════════════════════════════════════════════════════════════


class TestATSService:
    def test_detect(self, ats_service):
        result = ats_service.detect("https://boards.greenhouse.io/example")
        assert result is not None
        assert result.provider_name == "greenhouse"

    def test_detect_returns_none(self, ats_service):
        result = ats_service.detect("https://unknown.com")
        assert result is None

    def test_supports(self, ats_service):
        assert ats_service.supports("https://jobs.lever.co/company")
        assert not ats_service.supports("https://unknown.com")

    def test_get_provider(self, ats_service):
        provider = ats_service.get_provider("greenhouse")
        assert provider.name == "greenhouse"

    def test_get_provider_not_found(self, ats_service):
        with pytest.raises(ATSProviderNotFoundError):
            ats_service.get_provider("nonexistent")

    def test_get_provider_for_url(self, ats_service):
        provider = ats_service.get_provider_for_url("https://boards.greenhouse.io/example")
        assert provider is not None
        assert provider.name == "greenhouse"

    def test_list_providers(self, ats_service):
        providers = ats_service.list_providers()
        assert len(providers) == 7

    def test_get_provider_info(self, ats_service):
        info = ats_service.get_provider_info("greenhouse")
        assert info.name == "greenhouse"
        assert info.display_name == "Greenhouse"

    def test_get_provider_metadata(self, ats_service):
        meta = ats_service.get_provider_metadata("greenhouse")
        assert meta.name == "greenhouse"
        assert ATSProviderCapability.APPLY in meta.capabilities

    def test_login_creates_browser(self, ats_service, mock_browser):
        ats_service._browser = mock_browser
        result = ats_service.login("greenhouse", ATSLoginRequest(email="test@test.com", password="pass"))
        assert result.success
        mock_browser.create_browser.assert_called_once()
        mock_browser.close_browser.assert_called_once()

    def test_validate_creates_browser(self, ats_service, mock_browser):
        mock_browser.create_browser.return_value = {"id": "b1"}
        mock_browser.create_context.return_value = {"id": "c1"}
        mock_browser.create_session.return_value = {"id": "s1"}
        ats_service._browser = mock_browser
        ats_service.validate("greenhouse")
        mock_browser.create_browser.assert_called_once()
        mock_browser.close_browser.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════
#  Dependencies
# ═══════════════════════════════════════════════════════════════════════


class TestATSDependencies:
    def setup_method(self):
        reset_ats_service()

    def test_get_ats_service(self, mock_browser):
        with patch("app.ats.dependencies.get_browser_service", return_value=mock_browser):
            service = get_ats_service()
            assert isinstance(service, ATSService)

    def test_get_ats_service_singleton(self, mock_browser):
        with patch("app.ats.dependencies.get_browser_service", return_value=mock_browser):
            s1 = get_ats_service()
            s2 = get_ats_service()
            assert s1 is s2

    def test_reset_ats_service(self, mock_browser):
        with patch("app.ats.dependencies.get_browser_service", return_value=mock_browser):
            s1 = get_ats_service()
            reset_ats_service()
            s2 = get_ats_service()
            assert s1 is not s2

    def test_get_ats_service_initializes_providers(self, mock_browser):
        with patch("app.ats.dependencies.get_browser_service", return_value=mock_browser):
            service = get_ats_service()
            providers = service.list_providers()
            assert len(providers) > 0
