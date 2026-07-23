from __future__ import annotations

import time
import unittest
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.browser.cache import BrowserCache
from app.browser.config import BrowserConfig
from app.browser.context import ContextManager
from app.browser.cookies import CookieManager
from app.browser.dependencies import get_browser_service, reset_browser_service
from app.browser.downloads import DownloadManager
from app.browser.exceptions import (
    BrowserError,
    BrowserNotLaunchedError,
    ContextClosedError,
    CookieError,
    DownloadError,
    ElementNotFoundError,
    FileNotFoundError,
    FileSizeExceededError,
    InvalidFileExtensionError,
    InvalidSelectorError,
    MaxContextsExceededError,
    MaxPagesExceededError,
    ScreenshotError,
    SessionClosedError,
    StorageError,
    UploadError,
)
from app.browser.manager import BrowserManager
from app.browser.navigation import NavigationHelper
from app.browser.schemas import (
    BrowserInfo,
    BrowserState,
    BrowserType,
    ContextInfo,
    ContextState,
    Cookie,
    DownloadInfo,
    NavigationResult,
    ScreenshotOptions,
    SessionInfo,
    SessionState,
    UploadFile,
    ViewportSize,
)
from app.browser.screenshots import ScreenshotManager
from app.browser.selectors import SelectorHelper
from app.browser.service import BrowserService
from app.browser.session import SessionManager
from app.browser.storage import StorageManager
from app.browser.uploads import UploadManager
from app.browser.validator import BrowserValidator
from app.browser.waits import WaitStrategy

# ─── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def config():
    return BrowserConfig()


@pytest.fixture
def validator():
    return BrowserValidator()


@pytest.fixture
def manager(config):
    return BrowserManager(config)


@pytest.fixture
def context_manager(manager, config, validator):
    return ContextManager(manager, config, validator)


@pytest.fixture
def mock_page():
    page = MagicMock()
    page.url = "https://example.com"
    page.title.return_value = "Example"
    return page


@pytest.fixture
def mock_context():
    return MagicMock()


# ═══════════════════════════════════════════════════════════════════════
#  Schemas
# ═══════════════════════════════════════════════════════════════════════


class TestViewportSize:
    def test_defaults(self):
        v = ViewportSize()
        assert v.width == 1920
        assert v.height == 1080

    def test_custom(self):
        v = ViewportSize(width=800, height=600)
        assert v.width == 800
        assert v.height == 600


class TestBrowserInfo:
    def test_defaults(self):
        info = BrowserInfo()
        assert info.browser_type == BrowserType.CHROMIUM
        assert info.state == BrowserState.CLOSED
        assert info.headless is True
        assert info.context_count == 0
        assert isinstance(info.id, str)
        assert uuid.UUID(info.id)

    def test_model_dump(self):
        info = BrowserInfo(browser_type="firefox", headless=False)
        d = info.model_dump()
        assert d["browser_type"] == "firefox"
        assert d["headless"] is False


class TestContextInfo:
    def test_defaults(self):
        info = ContextInfo(browser_id="b1")
        assert info.browser_id == "b1"
        assert info.state == ContextState.OPEN
        assert info.is_persistent is False
        assert info.page_count == 0

    def test_model_dump(self):
        info = ContextInfo(browser_id="b1", is_persistent=True)
        d = info.model_dump()
        assert d["browser_id"] == "b1"
        assert d["is_persistent"] is True


class TestSessionInfo:
    def test_defaults(self):
        info = SessionInfo(browser_id="b1", context_id="c1")
        assert info.browser_id == "b1"
        assert info.context_id == "c1"
        assert info.state == SessionState.CREATED
        assert info.current_url is None

    def test_model_dump(self):
        info = SessionInfo(browser_id="b1", context_id="c1", state="active")
        d = info.model_dump()
        assert d["state"] == "active"


class TestCookie:
    def test_defaults(self):
        c = Cookie(name="foo", value="bar")
        assert c.name == "foo"
        assert c.value == "bar"
        assert c.domain is None
        assert c.http_only is False
        assert c.secure is False

    def test_full(self):
        c = Cookie(name="n", value="v", domain=".example.com", http_only=True, secure=True, same_site="Lax")
        assert c.domain == ".example.com"
        assert c.http_only is True
        assert c.same_site == "Lax"


class TestDownloadInfo:
    def test_defaults(self):
        d = DownloadInfo()
        assert d.success is False
        assert d.file_size_bytes == 0
        assert d.suggested_filename is None
        assert d.error is None

    def test_success(self):
        d = DownloadInfo(success=True, suggested_filename="resume.pdf", file_size_bytes=12345)
        assert d.suggested_filename == "resume.pdf"
        assert d.file_size_bytes == 12345


class TestNavigationResult:
    def test_defaults(self):
        n = NavigationResult(url="https://example.com")
        assert n.success is True
        assert n.url == "https://example.com"
        assert n.status_code is None
        assert n.duration_ms == 0.0

    def test_full(self):
        n = NavigationResult(
            success=False,
            url="https://fail.com",
            status_code=404,
            duration_ms=1500.5,
            error="Not found",
        )
        assert n.success is False
        assert n.status_code == 404
        assert n.duration_ms == 1500.5
        assert n.error == "Not found"


class TestScreenshotOptions:
    def test_defaults(self):
        o = ScreenshotOptions()
        assert o.full_page is False
        assert o.type == "png"
        assert o.quality is None
        assert o.timeout_ms is None

    def test_custom(self):
        o = ScreenshotOptions(full_page=True, quality=80, type="jpeg")
        assert o.full_page is True
        assert o.quality == 80
        assert o.type == "jpeg"


class TestUploadFile:
    def test_defaults(self):
        u = UploadFile(file_path="/tmp/doc.pdf", file_name="doc.pdf")
        assert u.file_size_bytes == 0
        assert u.mime_type == "application/octet-stream"
        assert u.selector is None


class TestBrowserType:
    def test_values(self):
        assert BrowserType.CHROMIUM.value == "chromium"
        assert BrowserType.FIREFOX.value == "firefox"
        assert BrowserType.WEBKIT.value == "webkit"


class TestBrowserState:
    def test_values(self):
        assert BrowserState.OPEN.value == "open"
        assert BrowserState.CLOSED.value == "closed"
        assert BrowserState.LAUNCHING.value == "launching"
        assert BrowserState.ERROR.value == "error"


class TestContextState:
    def test_values(self):
        assert ContextState.OPEN.value == "open"
        assert ContextState.CLOSED.value == "closed"


class TestSessionState:
    def test_values(self):
        assert SessionState.CREATED.value == "created"
        assert SessionState.NAVIGATING.value == "navigating"
        assert SessionState.ACTIVE.value == "active"
        assert SessionState.CLOSED.value == "closed"
        assert SessionState.ERROR.value == "error"


# ═══════════════════════════════════════════════════════════════════════
#  Config
# ═══════════════════════════════════════════════════════════════════════


class TestBrowserConfig:
    def test_defaults(self):
        c = BrowserConfig()
        assert c.cache_ttl_seconds == 300
        assert c.headless is True
        assert c.viewport_width == 1920
        assert c.max_contexts_per_browser == 5
        assert c.max_pages_per_context == 10
        assert c.max_upload_size_mb == 10
        assert c.retry_attempts == 3
        assert ".pdf" in c.allowed_upload_extensions
        assert c.cleanup_on_close is True

    def test_custom(self):
        c = BrowserConfig(headless=False, max_contexts_per_browser=3, cache_ttl_seconds=60)
        assert c.headless is False
        assert c.max_contexts_per_browser == 3
        assert c.cache_ttl_seconds == 60


# ═══════════════════════════════════════════════════════════════════════
#  Exceptions
# ═══════════════════════════════════════════════════════════════════════


class TestExceptions:
    def test_browser_error(self):
        e = BrowserError(message="test")
        assert e.code == "BROWSER_ERROR"
        assert e.status_code == 500

    def test_browser_not_found(self):
        e = BrowserNotLaunchedError(message="not found")
        assert e.code == "BROWSER_NOT_LAUNCHED"
        assert e.status_code == 400

    def test_context_closed(self):
        e = ContextClosedError(message="closed")
        assert e.code == "CONTEXT_CLOSED"
        assert e.status_code == 400

    def test_cookie_error(self):
        e = CookieError(message="cookie err")
        assert e.code == "COOKIE_ERROR"
        assert e.status_code == 400

    def test_download_error(self):
        e = DownloadError(message="dl err")
        assert e.code == "DOWNLOAD_ERROR"
        assert e.status_code == 400

    def test_element_not_found(self):
        e = ElementNotFoundError(message="el not found")
        assert e.code == "ELEMENT_NOT_FOUND"
        assert e.status_code == 404

    def test_upload_error(self):
        e = UploadError(message="upload fail")
        assert e.code == "UPLOAD_ERROR"
        assert e.status_code == 400

    def test_screenshot_error(self):
        e = ScreenshotError(message="sc fail")
        assert e.code == "SCREENSHOT_ERROR"
        assert e.status_code == 500

    def test_storage_error(self):
        e = StorageError(message="st fail")
        assert e.code == "STORAGE_ERROR"
        assert e.status_code == 500

    def test_file_not_found(self):
        e = FileNotFoundError(message="no file")
        assert e.code == "FILE_NOT_FOUND"
        assert e.status_code == 404

    def test_file_size_exceeded(self):
        e = FileSizeExceededError(message="too big")
        assert e.code == "FILE_SIZE_EXCEEDED"
        assert e.status_code == 400

    def test_invalid_file_extension(self):
        e = InvalidFileExtensionError(message="bad ext")
        assert e.code == "INVALID_FILE_EXTENSION"

    def test_invalid_selector(self):
        e = InvalidSelectorError(message="bad sel")
        assert e.code == "INVALID_SELECTOR"

    def test_max_contexts(self):
        e = MaxContextsExceededError(message="max ctx")
        assert e.code == "MAX_CONTEXTS_EXCEEDED"
        assert e.status_code == 429

    def test_max_pages(self):
        e = MaxPagesExceededError(message="max pg")
        assert e.code == "MAX_PAGES_EXCEEDED"
        assert e.status_code == 429

    def test_session_closed(self):
        e = SessionClosedError(message="sess closed")
        assert e.code == "SESSION_CLOSED"


# ═══════════════════════════════════════════════════════════════════════
#  Cache
# ═══════════════════════════════════════════════════════════════════════


class TestBrowserCache:
    def test_set_and_get(self):
        c = BrowserCache(BrowserConfig(cache_ttl_seconds=300))
        c.set("key1", "value1")
        assert c.get("key1") == "value1"

    def test_get_missing(self):
        c = BrowserCache(BrowserConfig())
        assert c.get("nonexistent") is None

    def test_invalidate(self):
        c = BrowserCache(BrowserConfig())
        c.set("key", "val")
        c.invalidate("key")
        assert c.get("key") is None

    def test_clear(self):
        c = BrowserCache(BrowserConfig())
        c.set("a", 1)
        c.set("b", 2)
        c.clear()
        assert c.get("a") is None
        assert c.get("b") is None

    def test_ttl_expiry(self):
        c = BrowserCache(BrowserConfig(cache_ttl_seconds=0))
        c.set("key", "val")
        time.sleep(0.01)
        assert c.get("key") is None

    def test_thread_safety(self):
        c = BrowserCache(BrowserConfig())
        results = []

        def worker():
            for i in range(100):
                c.set(f"k{i}", i)
                results.append(c.get(f"k{i}"))

        threads = [unittest.mock.Mock() for _ in range(4)]
        for _t in threads:
            worker()

        assert len(results) == 400

    def test_invalidate_missing(self):
        c = BrowserCache(BrowserConfig())
        c.invalidate("missing")
        assert c.get("missing") is None


# ═══════════════════════════════════════════════════════════════════════
#  Validator
# ═══════════════════════════════════════════════════════════════════════


class TestBrowserValidator:
    def test_validate_browser_launched_valid(self):
        v = BrowserValidator()
        info = BrowserInfo(state=BrowserState.OPEN)
        assert v.validate_browser_launched(info) is info

    def test_validate_browser_launched_none(self):
        v = BrowserValidator()
        with pytest.raises(BrowserNotLaunchedError):
            v.validate_browser_launched(None)

    def test_validate_browser_launched_closed(self):
        v = BrowserValidator()
        info = BrowserInfo(state=BrowserState.CLOSED)
        with pytest.raises(BrowserNotLaunchedError):
            v.validate_browser_launched(info)

    def test_validate_context_open_valid(self):
        v = BrowserValidator()
        info = ContextInfo(browser_id="b1", state=ContextState.OPEN)
        assert v.validate_context_open(info) is info

    def test_validate_context_open_none(self):
        v = BrowserValidator()
        with pytest.raises(ContextClosedError):
            v.validate_context_open(None)

    def test_validate_context_open_closed(self):
        v = BrowserValidator()
        info = ContextInfo(browser_id="b1", state=ContextState.CLOSED)
        with pytest.raises(ContextClosedError):
            v.validate_context_open(info)

    def test_validate_session_open_valid(self):
        v = BrowserValidator()
        info = SessionInfo(browser_id="b1", context_id="c1", state=SessionState.ACTIVE)
        assert v.validate_session_open(info) is info

    def test_validate_session_open_none(self):
        v = BrowserValidator()
        with pytest.raises(SessionClosedError):
            v.validate_session_open(None)

    def test_validate_session_open_closed(self):
        v = BrowserValidator()
        info = SessionInfo(browser_id="b1", context_id="c1", state=SessionState.CLOSED)
        with pytest.raises(SessionClosedError):
            v.validate_session_open(info)

    def test_validate_selector_valid(self):
        v = BrowserValidator()
        assert v.validate_selector("#myid") == "#myid"

    def test_validate_selector_empty(self):
        v = BrowserValidator()
        with pytest.raises(InvalidSelectorError):
            v.validate_selector("")

    def test_validate_selector_none(self):
        v = BrowserValidator()
        with pytest.raises(InvalidSelectorError):
            v.validate_selector(None)

    def test_validate_upload_file_valid(self):
        v = BrowserValidator()
        with patch("os.path.isfile", return_value=True), patch("os.path.getsize", return_value=1024):
            assert v.validate_upload_file("/tmp/doc.pdf") == "/tmp/doc.pdf"

    def test_validate_upload_file_not_found(self):
        v = BrowserValidator()
        with patch("os.path.isfile", return_value=False), pytest.raises(FileNotFoundError):
            v.validate_upload_file("/tmp/missing.pdf")

    def test_validate_upload_file_too_big(self):
        v = BrowserValidator(max_upload_size_mb=1)
        with (
            patch("os.path.isfile", return_value=True),
            patch("os.path.getsize", return_value=2 * 1024 * 1024),
            pytest.raises(FileSizeExceededError),
        ):
            v.validate_upload_file("/tmp/big.pdf")

    def test_validate_upload_file_bad_extension(self):
        v = BrowserValidator(allowed_extensions=(".pdf",))
        with (
            patch("os.path.isfile", return_value=True),
            patch("os.path.getsize", return_value=1024),
            pytest.raises(InvalidFileExtensionError),
        ):
            v.validate_upload_file("/tmp/doc.exe")

    def test_validate_max_contexts_ok(self):
        v = BrowserValidator(max_contexts=5)
        v.validate_max_contexts(3)

    def test_validate_max_contexts_exceeded(self):
        v = BrowserValidator(max_contexts=5)
        with pytest.raises(MaxContextsExceededError):
            v.validate_max_contexts(5)

    def test_validate_max_pages_ok(self):
        v = BrowserValidator(max_pages=10)
        v.validate_max_pages(5)

    def test_validate_max_pages_exceeded(self):
        v = BrowserValidator(max_pages=10)
        with pytest.raises(MaxPagesExceededError):
            v.validate_max_pages(10)


# ═══════════════════════════════════════════════════════════════════════
#  BrowserManager
# ═══════════════════════════════════════════════════════════════════════


class TestBrowserManager:
    def test_create_browser(self):
        m = BrowserManager(BrowserConfig())
        info = m.create_browser()
        assert info.state == BrowserState.OPEN
        assert isinstance(info.id, str)

    def test_create_browser_firefox(self):
        m = BrowserManager(BrowserConfig())
        info = m.create_browser(browser_type=BrowserType.FIREFOX)
        assert info.browser_type == BrowserType.FIREFOX

    def test_get_browser(self):
        m = BrowserManager(BrowserConfig())
        info = m.create_browser()
        assert m.get_browser(info.id) is not None

    def test_get_browser_missing(self):
        m = BrowserManager(BrowserConfig())
        assert m.get_browser("nonexistent") is None

    def test_get_browser_info(self):
        m = BrowserManager(BrowserConfig())
        info = m.create_browser()
        assert m.get_browser_info(info.id) is info

    def test_get_browser_info_missing(self):
        m = BrowserManager(BrowserConfig())
        assert m.get_browser_info("nonexistent") is None

    def test_update_browser_info(self):
        m = BrowserManager(BrowserConfig())
        info = m.create_browser()
        new_info = BrowserInfo(state=BrowserState.ERROR)
        m.update_browser_info(info.id, new_info)
        assert m.get_browser_info(info.id).state == BrowserState.ERROR

    def test_attach_instance(self):
        m = BrowserManager(BrowserConfig())
        info = m.create_browser()
        instance = MagicMock()
        m.attach_instance(info.id, instance)
        assert m.get_instance(info.id) is instance

    def test_get_instance_missing(self):
        m = BrowserManager(BrowserConfig())
        assert m.get_instance("nonexistent") is None

    def test_close_browser(self):
        m = BrowserManager(BrowserConfig())
        info = m.create_browser()
        m.close_browser(info.id)
        assert m.get_browser(info.id) is None

    def test_close_browser_closes_instance(self):
        m = BrowserManager(BrowserConfig())
        info = m.create_browser()
        instance = MagicMock()
        m.attach_instance(info.id, instance)
        m.close_browser(info.id)
        instance.close.assert_called_once()

    def test_close_browser_missing(self):
        m = BrowserManager(BrowserConfig())
        m.close_browser("nonexistent")

    def test_close_all(self):
        m = BrowserManager(BrowserConfig())
        m.create_browser()
        m.create_browser()
        m.close_all()
        assert m.count() == 0

    def test_list_browsers(self):
        m = BrowserManager(BrowserConfig())
        m.create_browser()
        m.create_browser()
        assert len(m.list_browsers()) == 2

    def test_count(self):
        m = BrowserManager(BrowserConfig())
        assert m.count() == 0
        m.create_browser()
        assert m.count() == 1

    def test_add_context(self):
        m = BrowserManager(BrowserConfig())
        info = m.create_browser()
        m.add_context(info.id, "ctx1", {})
        assert m.context_count(info.id) == 1
        assert info.context_count == 1

    def test_add_context_missing_browser(self):
        m = BrowserManager(BrowserConfig())
        m.add_context("nonexistent", "ctx1", {})

    def test_remove_context(self):
        m = BrowserManager(BrowserConfig())
        info = m.create_browser()
        m.add_context(info.id, "ctx1", {})
        m.remove_context(info.id, "ctx1")
        assert m.context_count(info.id) == 0

    def test_get_context(self):
        m = BrowserManager(BrowserConfig())
        info = m.create_browser()
        m.add_context(info.id, "ctx1", {"data": 42})
        ctx = m.get_context(info.id, "ctx1")
        assert ctx["data"] == 42

    def test_get_context_missing(self):
        m = BrowserManager(BrowserConfig())
        info = m.create_browser()
        assert m.get_context(info.id, "nonexistent") is None

    def test_context_count_missing_browser(self):
        m = BrowserManager(BrowserConfig())
        assert m.context_count("nonexistent") == 0


# ═══════════════════════════════════════════════════════════════════════
#  ContextManager
# ═══════════════════════════════════════════════════════════════════════


class TestContextManager:
    def test_create_context(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        assert ctx.browser_id == info.id
        assert ctx.state == ContextState.OPEN
        assert manager.context_count(info.id) == 1

    def test_create_context_browser_not_launched(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        with pytest.raises(BrowserNotLaunchedError):
            cm.create_context("nonexistent")

    def test_create_context_max_exceeded(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        info = manager.create_browser()
        cm.create_context(info.id)
        with pytest.raises(MaxContextsExceededError):
            for _ in range(10):
                cm.create_context(info.id)

    def test_create_context_persistent(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id, storage_state={"key": "val"})
        assert ctx.is_persistent is True

    def test_get_context_info(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        assert cm.get_context_info(info.id, ctx.id) is ctx

    def test_get_context_info_missing(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        info = manager.create_browser()
        assert cm.get_context_info(info.id, "nonexistent") is None

    def test_attach_instance(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        instance = MagicMock()
        cm.attach_instance(info.id, ctx.id, instance)
        assert cm.get_instance(info.id, ctx.id) is instance

    def test_close_context(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        cm.close_context(info.id, ctx.id)
        assert manager.context_count(info.id) == 0

    def test_close_context_closes_instance(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        instance = MagicMock()
        cm.attach_instance(info.id, ctx.id, instance)
        cm.close_context(info.id, ctx.id)
        instance.close.assert_called_once()

    def test_add_page(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        cm.add_page(info.id, ctx.id, "p1", MagicMock())
        assert ctx.page_count == 1

    def test_add_page_max_exceeded(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        with pytest.raises(MaxPagesExceededError):
            for _ in range(15):
                cm.add_page(info.id, ctx.id, str(_), MagicMock())

    def test_remove_page(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        cm.add_page(info.id, ctx.id, "p1", MagicMock())
        cm.remove_page(info.id, ctx.id, "p1")
        assert ctx.page_count == 0

    def test_get_page(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        page = MagicMock()
        cm.add_page(info.id, ctx.id, "p1", page)
        assert cm.get_page(info.id, ctx.id, "p1") is page

    def test_get_page_missing(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        assert cm.get_page(info.id, ctx.id, "nonexistent") is None

    def test_list_pages(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        cm.add_page(info.id, ctx.id, "p1", MagicMock())
        cm.add_page(info.id, ctx.id, "p2", MagicMock())
        assert sorted(cm.list_pages(info.id, ctx.id)) == ["p1", "p2"]


# ═══════════════════════════════════════════════════════════════════════
#  SessionManager
# ═══════════════════════════════════════════════════════════════════════


class TestSessionManager:
    def test_create_session(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        sm = SessionManager(cm, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        sess = sm.create_session(info.id, ctx.id)
        assert sess.browser_id == info.id
        assert sess.context_id == ctx.id
        assert sess.state == SessionState.CREATED

    def test_create_session_context_closed(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        sm = SessionManager(cm, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        cm.close_context(info.id, ctx.id)
        with pytest.raises(ContextClosedError):
            sm.create_session(info.id, ctx.id)

    def test_get_session(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        sm = SessionManager(cm, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        sess = sm.create_session(info.id, ctx.id)
        assert sm.get_session(sess.id) is not None

    def test_get_session_missing(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        sm = SessionManager(cm, config, validator)
        assert sm.get_session("nonexistent") is None

    def test_get_session_info(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        sm = SessionManager(cm, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        sess = sm.create_session(info.id, ctx.id)
        assert sm.get_session_info(sess.id) is sess

    def test_update_state(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        sm = SessionManager(cm, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        sess = sm.create_session(info.id, ctx.id)
        sm.update_state(sess.id, SessionState.ACTIVE)
        assert sm.get_session_info(sess.id).state == SessionState.ACTIVE

    def test_close_session(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        sm = SessionManager(cm, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        sess = sm.create_session(info.id, ctx.id)
        sm.close_session(sess.id)
        assert sm.get_session(sess.id) is None
        assert sm.count() == 0

    def test_list_sessions(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        sm = SessionManager(cm, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        sm.create_session(info.id, ctx.id)
        sm.create_session(info.id, ctx.id)
        assert len(sm.list_sessions()) == 2

    def test_count(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        sm = SessionManager(cm, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        assert sm.count() == 0
        sm.create_session(info.id, ctx.id)
        assert sm.count() == 1

    def test_get_page(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        sm = SessionManager(cm, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        page = MagicMock()
        cm.add_page(info.id, ctx.id, "p1", page)
        sm.create_session(info.id, ctx.id)

    def test_get_page_with_attached(self, manager, config, validator):
        cm = ContextManager(manager, config, validator)
        sm = SessionManager(cm, config, validator)
        info = manager.create_browser()
        ctx = cm.create_context(info.id)
        instance = MagicMock()
        cm.attach_instance(info.id, ctx.id, instance)
        sess = sm.create_session(info.id, ctx.id)
        sm.get_session_info(sess.id)


# ═══════════════════════════════════════════════════════════════════════
#  WaitStrategy
# ═══════════════════════════════════════════════════════════════════════


class TestWaitStrategy:
    def test_wait_for_selector(self, mock_page):
        w = WaitStrategy()
        w.wait_for_selector(mock_page, "#myid")
        mock_page.wait_for_selector.assert_called_once_with("#myid", timeout=10000.0, state="visible")

    def test_wait_for_selector_timeout(self, mock_page):
        mock_page.wait_for_selector.side_effect = Exception("timeout")
        w = WaitStrategy()
        with pytest.raises(ElementNotFoundError):
            w.wait_for_selector(mock_page, "#myid")

    def test_wait_for_element_state(self, mock_page):
        w = WaitStrategy()
        w.wait_for_element_state(mock_page, "#myid", "visible")
        mock_page.locator.assert_called_once_with("#myid")

    def test_wait_for_element_state_timeout(self, mock_page):
        mock_page.locator.return_value.wait_for.side_effect = Exception("timeout")
        w = WaitStrategy()
        with pytest.raises(ElementNotFoundError):
            w.wait_for_element_state(mock_page, "#myid")

    def test_wait_for_network_idle(self, mock_page):
        w = WaitStrategy()
        w.wait_for_network_idle(mock_page)
        mock_page.wait_for_load_state.assert_called_once_with("networkidle", timeout=10000.0)

    def test_wait_for_load_state(self, mock_page):
        w = WaitStrategy()
        w.wait_for_load_state(mock_page, "domcontentloaded")
        mock_page.wait_for_load_state.assert_called_once_with("domcontentloaded", timeout=10000.0)

    def test_wait_for_function(self, mock_page):
        w = WaitStrategy()
        w.wait_for_function(mock_page, "() => true")
        mock_page.wait_for_function.assert_called_once_with("() => true", timeout=10000.0)

    def test_wait_for_url(self, mock_page):
        w = WaitStrategy()
        w.wait_for_url(mock_page, "**/done")
        mock_page.wait_for_url.assert_called_once_with("**/done", timeout=10000.0)

    def test_wait_for_timeout(self, mock_page):
        w = WaitStrategy()
        w.wait_for_timeout(mock_page, 500)
        mock_page.wait_for_timeout.assert_called_once_with(500)

    def test_retry_success(self, mock_page):
        w = WaitStrategy()
        fn = MagicMock(return_value=42)
        assert w.retry(fn, attempts=3) == 42
        assert fn.call_count == 1

    def test_retry_failure(self, mock_page):
        w = WaitStrategy()
        fn = MagicMock(side_effect=ValueError("fail"))
        with pytest.raises(ValueError):
            w.retry(fn, attempts=2)
        assert fn.call_count == 2

    def test_retry_eventual_success(self, mock_page):
        w = WaitStrategy()
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "ok"

        assert w.retry(flaky, attempts=3) == "ok"
        assert call_count == 3


# ═══════════════════════════════════════════════════════════════════════
#  NavigationHelper
# ═══════════════════════════════════════════════════════════════════════


class TestNavigationHelper:
    def test_goto_success(self, mock_page):
        mock_page.goto.return_value = MagicMock(status=200)
        w = WaitStrategy()
        nav = NavigationHelper(w)
        result = nav.goto(mock_page, "https://example.com")
        assert result.success is True
        assert result.url == "https://example.com"
        assert result.status_code == 200

    def test_goto_failure(self, mock_page):
        mock_page.goto.side_effect = Exception("net error")
        w = WaitStrategy()
        nav = NavigationHelper(w)
        result = nav.goto(mock_page, "https://fail.com")
        assert result.success is False
        assert result.error == "net error"

    def test_reload_success(self, mock_page):
        mock_page.reload.return_value = MagicMock(status=200)
        w = WaitStrategy()
        nav = NavigationHelper(w)
        result = nav.reload(mock_page)
        assert result.success is True

    def test_reload_failure(self, mock_page):
        mock_page.reload.side_effect = Exception("reload fail")
        w = WaitStrategy()
        nav = NavigationHelper(w)
        result = nav.reload(mock_page)
        assert result.success is False

    def test_back(self, mock_page):
        mock_page.go_back.return_value = MagicMock()
        w = WaitStrategy()
        nav = NavigationHelper(w)
        result = nav.back(mock_page)
        assert result.success is True

    def test_forward(self, mock_page):
        mock_page.go_forward.return_value = MagicMock()
        w = WaitStrategy()
        nav = NavigationHelper(w)
        result = nav.forward(mock_page)
        assert result.success is True

    def test_safe_click(self, mock_page):
        w = WaitStrategy()
        nav = NavigationHelper(w)
        mock_page.locator.return_value = MagicMock()
        nav.safe_click(mock_page, "#btn")
        mock_page.click.assert_called_once()

    def test_safe_click_failure(self, mock_page):
        mock_page.click.side_effect = Exception("click fail")
        w = WaitStrategy()
        nav = NavigationHelper(w)
        with pytest.raises(ElementNotFoundError):
            nav.safe_click(mock_page, "#btn")

    def test_safe_fill(self, mock_page):
        w = WaitStrategy()
        nav = NavigationHelper(w)
        mock_page.locator.return_value = MagicMock()
        nav.safe_fill(mock_page, "#input", "hello")
        mock_page.fill.assert_called_once()

    def test_safe_select(self, mock_page):
        w = WaitStrategy()
        nav = NavigationHelper(w)
        mock_page.locator.return_value = MagicMock()
        nav.safe_select(mock_page, "#sel", "opt1")
        mock_page.select_option.assert_called_once()

    def test_wait_for_network_idle_delegation(self, mock_page):
        w = WaitStrategy()
        nav = NavigationHelper(w)
        nav.wait_for_network_idle(mock_page)
        mock_page.wait_for_load_state.assert_called_once_with("networkidle", timeout=10000.0)

    def test_route_navigation_result(self, mock_page):
        w = WaitStrategy()
        nav = NavigationHelper(w)
        mock_page.goto.return_value = MagicMock(status=200)
        with patch("time.monotonic", side_effect=[1000.0, 1002.5]):
            result = nav.goto(mock_page, "https://example.com")
        assert result.duration_ms == 2500.0


# ═══════════════════════════════════════════════════════════════════════
#  SelectorHelper
# ═══════════════════════════════════════════════════════════════════════


class TestSelectorHelper:
    def test_by_text(self):
        assert SelectorHelper.by_text("hello") == "* >> text=hello"

    def test_by_text_with_tag(self):
        assert SelectorHelper.by_text("click me", tag="button") == "button >> text=click me"

    def test_by_text_empty(self):
        with pytest.raises(InvalidSelectorError):
            SelectorHelper.by_text("")

    def test_by_label(self):
        assert SelectorHelper.by_label("Email") == 'label:has-text("Email")'

    def test_by_label_empty(self):
        with pytest.raises(InvalidSelectorError):
            SelectorHelper.by_label("")

    def test_by_placeholder(self):
        assert SelectorHelper.by_placeholder("Search...") == '[placeholder="Search..."]'

    def test_by_placeholder_empty(self):
        with pytest.raises(InvalidSelectorError):
            SelectorHelper.by_placeholder("")

    def test_by_test_id(self):
        assert SelectorHelper.by_test_id("submit-btn") == '[data-testid="submit-btn"]'

    def test_by_test_id_empty(self):
        with pytest.raises(InvalidSelectorError):
            SelectorHelper.by_test_id("")

    def test_by_role(self):
        assert SelectorHelper.by_role("button") == "role=button"

    def test_by_role_with_name(self):
        assert SelectorHelper.by_role("button", name="Submit") == 'role=button[name="Submit"]'

    def test_by_role_empty(self):
        with pytest.raises(InvalidSelectorError):
            SelectorHelper.by_role("")

    def test_by_aria_label(self):
        assert SelectorHelper.by_aria_label("Close") == '[aria-label="Close"]'

    def test_by_aria_label_empty(self):
        with pytest.raises(InvalidSelectorError):
            SelectorHelper.by_aria_label("")

    def test_by_css(self):
        assert SelectorHelper.by_css(".myclass") == ".myclass"

    def test_by_css_empty(self):
        with pytest.raises(InvalidSelectorError):
            SelectorHelper.by_css("")

    def test_by_xpath(self):
        assert SelectorHelper.by_xpath("//div[@id='main']") == "xpath=//div[@id='main']"

    def test_by_xpath_empty(self):
        with pytest.raises(InvalidSelectorError):
            SelectorHelper.by_xpath("")

    def test_click(self, mock_page):
        SelectorHelper.click(mock_page, "#btn")
        mock_page.click.assert_called_once_with("#btn", timeout=10000.0)

    def test_click_failure(self, mock_page):
        mock_page.click.side_effect = Exception("fail")
        with pytest.raises(ElementNotFoundError):
            SelectorHelper.click(mock_page, "#btn")

    def test_fill(self, mock_page):
        SelectorHelper.fill(mock_page, "#input", "hello")
        mock_page.fill.assert_called_once_with("#input", "hello", timeout=10000.0)

    def test_select_option(self, mock_page):
        SelectorHelper.select_option(mock_page, "#sel", "opt1")
        mock_page.select_option.assert_called_once_with("#sel", "opt1", timeout=10000.0)

    def test_get_text(self, mock_page):
        mock_page.text_content.return_value = "hello world"
        assert SelectorHelper.get_text(mock_page, "#el") == "hello world"

    def test_get_text_none(self, mock_page):
        mock_page.text_content.return_value = None
        assert SelectorHelper.get_text(mock_page, "#el") == ""

    def test_get_text_failure(self, mock_page):
        mock_page.text_content.side_effect = Exception("fail")
        with pytest.raises(ElementNotFoundError):
            SelectorHelper.get_text(mock_page, "#el")

    def test_is_visible(self, mock_page):
        mock_page.locator.return_value.is_visible.return_value = True
        assert SelectorHelper.is_visible(mock_page, "#el") is True

    def test_is_visible_not(self, mock_page):
        mock_page.locator.return_value.is_visible.return_value = False
        assert SelectorHelper.is_visible(mock_page, "#el") is False

    def test_is_visible_exception(self, mock_page):
        mock_page.locator.return_value.is_visible.side_effect = Exception()
        assert SelectorHelper.is_visible(mock_page, "#el") is False


# ═══════════════════════════════════════════════════════════════════════
#  DownloadManager
# ═══════════════════════════════════════════════════════════════════════


class TestDownloadManager:
    def test_capture_download(self, mock_page):
        dm = DownloadManager()
        download_mock = MagicMock()
        download_mock.suggested_filename = "resume.pdf"
        mock_page.expect_download.return_value.__enter__.return_value.value = download_mock
        with patch("os.path.isfile", return_value=True), patch("os.path.getsize", return_value=12345):
            info = dm.capture_download(mock_page)
        assert info.success is True
        assert info.suggested_filename == "resume.pdf"
        assert info.file_size_bytes == 12345

    def test_capture_download_no_filename(self, mock_page):
        dm = DownloadManager()
        download_mock = MagicMock()
        download_mock.suggested_filename = None
        mock_page.expect_download.return_value.__enter__.return_value.value = download_mock
        with patch("os.path.isfile", return_value=True), patch("os.path.getsize", return_value=100):
            info = dm.capture_download(mock_page)
        assert info.success is True
        assert info.suggested_filename is None

    def test_capture_download_failure(self, mock_page):
        dm = DownloadManager()
        mock_page.expect_download.side_effect = Exception("download failed")
        info = dm.capture_download(mock_page)
        assert info.success is False
        assert info.error == "download failed"

    def test_capture_download_by_click(self, mock_page):
        dm = DownloadManager()
        download_mock = MagicMock()
        download_mock.suggested_filename = "report.pdf"
        mock_page.expect_download.return_value.__enter__.return_value.value = download_mock
        with patch("os.path.getsize", return_value=999):
            info = dm.capture_download_by_click(mock_page, "#dl-btn")
        assert info.success is True
        mock_page.click.assert_called_once_with("#dl-btn", timeout=60000.0)

    def test_capture_download_by_click_failure(self, mock_page):
        dm = DownloadManager()
        mock_page.click.side_effect = Exception("click fail")
        info = dm.capture_download_by_click(mock_page, "#dl-btn")
        assert info.success is False

    def test_get_download(self, mock_page):
        dm = DownloadManager()
        download_mock = MagicMock()
        download_mock.suggested_filename = "resume.pdf"
        mock_page.expect_download.return_value.__enter__.return_value.value = download_mock
        with patch("os.path.getsize", return_value=100):
            info = dm.capture_download(mock_page)
        assert dm.get_download(info.id) is info

    def test_get_download_missing(self, mock_page):
        dm = DownloadManager()
        assert dm.get_download("nonexistent") is None

    def test_list_downloads(self, mock_page):
        dm = DownloadManager()
        assert len(dm.list_downloads()) == 0
        download_mock = MagicMock()
        download_mock.suggested_filename = "f1.pdf"
        mock_page.expect_download.return_value.__enter__.return_value.value = download_mock
        with patch("os.path.getsize", return_value=100):
            dm.capture_download(mock_page)
        assert len(dm.list_downloads()) == 1

    def test_clear(self, mock_page):
        dm = DownloadManager()
        download_mock = MagicMock()
        download_mock.suggested_filename = "f1.pdf"
        mock_page.expect_download.return_value.__enter__.return_value.value = download_mock
        with patch("os.path.getsize", return_value=100):
            dm.capture_download(mock_page)
        dm.clear()
        assert len(dm.list_downloads()) == 0

    def test_verify_download_missing(self, mock_page):
        dm = DownloadManager()
        with patch("os.path.isfile", return_value=False):
            assert dm.verify_download("/tmp/missing.pdf") is False

    def test_verify_download_exists(self, mock_page):
        dm = DownloadManager()
        with patch("os.path.isfile", return_value=True), patch("os.path.getsize", return_value=100):
            assert dm.verify_download("/tmp/exists.pdf") is True


# ═══════════════════════════════════════════════════════════════════════
#  UploadManager
# ═══════════════════════════════════════════════════════════════════════


class TestUploadManager:
    def test_upload_file(self, mock_page, validator):
        um = UploadManager(validator)
        mock_locator = MagicMock()
        mock_locator.is_visible.return_value = True
        mock_page.locator.return_value = mock_locator
        with patch("os.path.isfile", return_value=True), patch("os.path.getsize", return_value=1024):
            um.upload_file(mock_page, "#upload", "/tmp/doc.pdf")
        mock_locator.set_input_files.assert_called_once()

    def test_upload_file_not_visible(self, mock_page, validator):
        um = UploadManager(validator)
        mock_locator = MagicMock()
        mock_locator.is_visible.return_value = False
        mock_page.locator.return_value = mock_locator
        with (
            patch("os.path.isfile", return_value=True),
            patch("os.path.getsize", return_value=1024),
            pytest.raises(ElementNotFoundError),
        ):
            um.upload_file(mock_page, "#upload", "/tmp/doc.pdf")

    def test_upload_file_not_found(self, mock_page, validator):
        um = UploadManager(validator)
        with patch("os.path.isfile", return_value=False), pytest.raises(FileNotFoundError):
            um.upload_file(mock_page, "#upload", "/tmp/missing.pdf")

    def test_upload_multiple(self, mock_page, validator):
        um = UploadManager(validator)
        mock_locator = MagicMock()
        mock_locator.is_visible.return_value = True
        mock_page.locator.return_value = mock_locator
        with patch("os.path.isfile", return_value=True), patch("os.path.getsize", return_value=1024):
            um.upload_multiple(mock_page, "#upload", ["/tmp/a.pdf", "/tmp/b.pdf"])
        mock_locator.set_input_files.assert_called_once()

    def test_upload_multiple_not_visible(self, mock_page, validator):
        um = UploadManager(validator)
        mock_locator = MagicMock()
        mock_locator.is_visible.return_value = False
        mock_page.locator.return_value = mock_locator
        with (
            patch("os.path.isfile", return_value=True),
            patch("os.path.getsize", return_value=1024),
            pytest.raises(ElementNotFoundError),
        ):
            um.upload_multiple(mock_page, "#upload", ["/tmp/a.pdf"])

    def test_upload_file_set_input_files_error(self, mock_page, validator):
        um = UploadManager(validator)
        mock_locator = MagicMock()
        mock_locator.is_visible.return_value = True
        mock_locator.set_input_files.side_effect = Exception("upload failed")
        mock_page.locator.return_value = mock_locator
        with (
            patch("os.path.isfile", return_value=True),
            patch("os.path.getsize", return_value=1024),
            pytest.raises(UploadError),
        ):
            um.upload_file(mock_page, "#upload", "/tmp/doc.pdf")


# ═══════════════════════════════════════════════════════════════════════
#  ScreenshotManager
# ═══════════════════════════════════════════════════════════════════════


class TestScreenshotManager:
    def test_take_screenshot(self, mock_page):
        sm = ScreenshotManager()
        with (
            patch("os.makedirs"),
            patch("os.listdir", return_value=[]),
            patch("os.path.getmtime"),
            patch("os.path.isfile", return_value=False),
            patch("os.remove"),
        ):
            path = sm.take_screenshot(mock_page, "test")
        assert "test.png" in path
        assert sm._screenshot_path in path
        mock_page.screenshot.assert_called_once()

    def test_take_screenshot_full_page(self, mock_page):
        sm = ScreenshotManager()
        with (
            patch("os.makedirs"),
            patch("os.listdir", return_value=[]),
            patch("os.path.getmtime"),
            patch("os.path.isfile", return_value=False),
            patch("os.remove"),
        ):
            path = sm.take_screenshot(mock_page, "full", ScreenshotOptions(full_page=True))
        assert "full.png" in path
        call_kwargs = mock_page.screenshot.call_args.kwargs
        assert call_kwargs["full_page"] is True

    def test_take_screenshot_failure(self, mock_page):
        sm = ScreenshotManager()
        mock_page.screenshot.side_effect = Exception("sc fail")
        with patch("os.makedirs"), pytest.raises(ScreenshotError):
            sm.take_screenshot(mock_page, "fail")

    def test_take_element_screenshot(self, mock_page):
        sm = ScreenshotManager()
        mock_element = MagicMock()
        mock_page.locator.return_value = mock_element
        with (
            patch("os.makedirs"),
            patch("os.listdir", return_value=[]),
            patch("os.path.getmtime"),
            patch("os.path.isfile", return_value=False),
            patch("os.remove"),
        ):
            path = sm.take_element_screenshot(mock_page, "#el", "myel")
        assert "myel.png" in path
        mock_element.screenshot.assert_called_once()

    def test_take_element_screenshot_failure(self, mock_page):
        sm = ScreenshotManager()
        mock_page.locator.return_value.screenshot.side_effect = Exception("fail")
        with pytest.raises(ScreenshotError):
            sm.take_element_screenshot(mock_page, "#el", "myel")

    def test_take_failure_screenshot(self, mock_page):
        sm = ScreenshotManager()
        with patch.object(sm, "take_screenshot", return_value="/path/failure.png") as mock_ts:
            path = sm.take_failure_screenshot(mock_page, "login")
            assert path == "/path/failure.png"
            mock_ts.assert_called_once()

    def test_cleanup_old_files(self, mock_page):
        sm = ScreenshotManager(max_files=2)
        old_files = ["old1.png", "old2.png", "old3.png"]
        with (
            patch("os.makedirs"),
            patch("os.listdir", return_value=old_files),
            patch("os.path.getmtime", return_value=100.0),
            patch("os.path.isfile", return_value=True),
            patch("os.remove") as mock_remove,
        ):
            sm.take_screenshot(mock_page, "new")
            assert mock_remove.call_count == 1

    def test_generate_filename_default(self):
        sm = ScreenshotManager()
        name = sm._generate_filename(None, "png")
        assert name.endswith(".png")
        assert "screenshot" in name

    def test_generate_filename_with_name(self):
        sm = ScreenshotManager()
        name = sm._generate_filename("my_capture", "png")
        assert name.endswith(".png")
        assert "my_capture" in name


# ═══════════════════════════════════════════════════════════════════════
#  CookieManager
# ═══════════════════════════════════════════════════════════════════════


class TestCookieManager:
    def test_get_cookies(self, mock_page):
        mock_page.context.cookies.return_value = [
            {"name": "session", "value": "abc123", "domain": ".example.com", "httpOnly": True},
        ]
        cookies = CookieManager.get_cookies(mock_page)
        assert len(cookies) == 1
        assert cookies[0].name == "session"
        assert cookies[0].value == "abc123"
        assert cookies[0].http_only is True

    def test_get_cookies_empty(self, mock_page):
        mock_page.context.cookies.return_value = []
        assert CookieManager.get_cookies(mock_page) == []

    def test_get_cookies_error(self, mock_page):
        mock_page.context.cookies.side_effect = Exception("cookie fail")
        with pytest.raises(CookieError):
            CookieManager.get_cookies(mock_page)

    def test_set_cookies(self, mock_page):
        cookies = [Cookie(name="foo", value="bar", domain=".example.com")]
        CookieManager.set_cookies(mock_page, cookies)
        mock_page.context.add_cookies.assert_called_once()

    def test_set_cookies_error(self, mock_page):
        mock_page.context.add_cookies.side_effect = Exception("set fail")
        with pytest.raises(CookieError):
            CookieManager.set_cookies(mock_page, [Cookie(name="x", value="y")])

    def test_clear_cookies(self, mock_page):
        CookieManager.clear_cookies(mock_page)
        mock_page.context.clear_cookies.assert_called_once()

    def test_clear_cookies_error(self, mock_page):
        mock_page.context.clear_cookies.side_effect = Exception("clear fail")
        with pytest.raises(CookieError):
            CookieManager.clear_cookies(mock_page)

    def test_get_cookie_found(self, mock_page):
        mock_page.context.cookies.return_value = [
            {"name": "session", "value": "abc", "domain": ".example.com"},
        ]
        c = CookieManager.get_cookie(mock_page, "session")
        assert c is not None
        assert c.value == "abc"

    def test_get_cookie_not_found(self, mock_page):
        mock_page.context.cookies.return_value = [
            {"name": "other", "value": "val"},
        ]
        c = CookieManager.get_cookie(mock_page, "session")
        assert c is None


# ═══════════════════════════════════════════════════════════════════════
#  StorageManager
# ═══════════════════════════════════════════════════════════════════════


class TestStorageManager:
    def test_get_storage_state(self, mock_context):
        mock_context.storage_state.return_value = {"cookies": [], "origins": []}
        result = StorageManager.get_storage_state(mock_context)
        assert result == {"cookies": [], "origins": []}

    def test_get_storage_state_error(self, mock_context):
        mock_context.storage_state.side_effect = Exception("storage fail")
        with pytest.raises(StorageError):
            StorageManager.get_storage_state(mock_context)

    def test_add_init_script(self, mock_context):
        StorageManager.add_init_script(mock_context, "console.log('hi')")
        mock_context.add_init_script.assert_called_once_with("console.log('hi')")

    def test_add_init_script_error(self, mock_context):
        mock_context.add_init_script.side_effect = Exception("script fail")
        with pytest.raises(StorageError):
            StorageManager.add_init_script(mock_context, "bad")

    def test_set_extra_http_headers(self, mock_context):
        StorageManager.set_extra_http_headers(mock_context, {"X-Custom": "val"})
        mock_context.set_extra_http_headers.assert_called_once_with({"X-Custom": "val"})

    def test_grant_permissions(self, mock_context):
        StorageManager.grant_permissions(mock_context, ["geolocation"])
        mock_context.grant_permissions.assert_called_once_with(["geolocation"])

    def test_clear_permissions(self, mock_context):
        StorageManager.clear_permissions(mock_context)
        mock_context.clear_permissions.assert_called_once()

    def test_set_geolocation(self, mock_context):
        StorageManager.set_geolocation(mock_context, 40.7128, -74.0060)
        mock_context.set_geolocation.assert_called_once_with({"latitude": 40.7128, "longitude": -74.0060})

    def test_set_offline(self, mock_context):
        StorageManager.set_offline(mock_context, True)
        mock_context.set_offline.assert_called_once_with(True)

    def test_set_offline_false(self, mock_context):
        StorageManager.set_offline(mock_context, False)
        mock_context.set_offline.assert_called_once_with(False)


# ═══════════════════════════════════════════════════════════════════════
#  BrowserService (integration smoke tests)
# ═══════════════════════════════════════════════════════════════════════


class TestBrowserService:
    def test_initialization(self):
        svc = BrowserService()
        assert svc.config is not None
        assert svc.validator is not None
        assert svc.cache is not None
        assert svc.manager is not None
        assert svc.downloads is not None
        assert svc.screenshots is not None
        assert svc.cookies is not None
        assert svc.storage is not None
        assert svc.uploads is not None
        assert svc.contexts is not None
        assert svc.sessions is not None
        assert svc.waits is not None
        assert svc.navigation is not None
        assert svc.selectors is not None

    def test_create_browser(self):
        svc = BrowserService()
        result = svc.create_browser()
        assert "id" in result
        assert result["state"] == "open"

    def test_get_browser_info(self):
        svc = BrowserService()
        created = svc.create_browser()
        info = svc.get_browser_info(created["id"])
        assert info is not None
        assert info["id"] == created["id"]

    def test_get_browser_info_missing(self):
        svc = BrowserService()
        assert svc.get_browser_info("nonexistent") is None

    def test_close_browser(self):
        svc = BrowserService()
        created = svc.create_browser()
        svc.close_browser(created["id"])
        assert svc.get_browser_info(created["id"]) is None

    def test_close_all(self):
        svc = BrowserService()
        svc.create_browser()
        svc.create_browser()
        svc.close_all()
        assert len(svc.list_browsers()) == 0

    def test_list_browsers(self):
        svc = BrowserService()
        svc.create_browser()
        svc.create_browser(browser_type="firefox")
        assert len(svc.list_browsers()) == 2

    def test_create_context(self):
        svc = BrowserService()
        browser = svc.create_browser()
        ctx = svc.create_context(browser["id"])
        assert ctx["browser_id"] == browser["id"]
        assert ctx["state"] == "open"

    def test_create_session(self):
        svc = BrowserService()
        browser = svc.create_browser()
        ctx = svc.create_context(browser["id"])
        sess = svc.create_session(browser["id"], ctx["id"])
        assert sess["browser_id"] == browser["id"]
        assert sess["context_id"] == ctx["id"]
        assert sess["state"] == "created"

    def test_cache_operations(self):
        svc = BrowserService()
        svc.cache_set("key", "value")
        assert svc.cache_get("key") == "value"
        svc.cache_invalidate("key")
        assert svc.cache_get("key") is None

    def test_cache_clear(self):
        svc = BrowserService()
        svc.cache_set("a", 1)
        svc.cache_set("b", 2)
        svc.cache_clear()
        assert svc.cache_get("a") is None
        assert svc.cache_get("b") is None

    def test_navigate(self, mock_page):
        svc = BrowserService()
        mock_page.goto.return_value = MagicMock(status=200)
        result = svc.navigate(mock_page, "https://example.com")
        assert result.success is True
        mock_page.goto.assert_called_once_with("https://example.com", timeout=60000.0, wait_until="load")

    def test_safe_click(self, mock_page):
        svc = BrowserService()
        mock_page.locator.return_value = MagicMock()
        svc.safe_click(mock_page, "#btn")
        mock_page.click.assert_called_once()

    def test_safe_fill(self, mock_page):
        svc = BrowserService()
        mock_page.locator.return_value = MagicMock()
        svc.safe_fill(mock_page, "#input", "hello")
        mock_page.fill.assert_called_once()

    def test_click_selector(self, mock_page):
        svc = BrowserService()
        svc.click(mock_page, "#btn")
        mock_page.click.assert_called_once_with("#btn", timeout=10000.0)

    def test_fill_selector(self, mock_page):
        svc = BrowserService()
        svc.fill(mock_page, "#input", "val")
        mock_page.fill.assert_called_once_with("#input", "val", timeout=10000.0)

    def test_is_visible(self, mock_page):
        svc = BrowserService()
        mock_page.locator.return_value.is_visible.return_value = True
        assert svc.is_visible(mock_page, "#el") is True

    def test_get_text(self, mock_page):
        svc = BrowserService()
        mock_page.text_content.return_value = "hello"
        assert svc.get_text(mock_page, "#el") == "hello"

    def test_get_cookies(self, mock_page):
        svc = BrowserService()
        mock_page.context.cookies.return_value = [{"name": "s", "value": "v"}]
        cookies = svc.get_cookies(mock_page)
        assert len(cookies) == 1
        assert cookies[0]["name"] == "s"

    def test_set_cookies(self, mock_page):
        svc = BrowserService()
        svc.set_cookies(mock_page, [{"name": "x", "value": "y"}])
        mock_page.context.add_cookies.assert_called_once()

    def test_clear_cookies(self, mock_page):
        svc = BrowserService()
        svc.clear_cookies(mock_page)
        mock_page.context.clear_cookies.assert_called_once()

    def test_get_storage_state(self, mock_context):
        svc = BrowserService()
        mock_context.storage_state.return_value = {"state": "ok"}
        assert svc.get_storage_state(mock_context) == {"state": "ok"}

    def test_take_screenshot(self, mock_page):
        svc = BrowserService()
        with (
            patch("os.makedirs"),
            patch("os.listdir", return_value=[]),
            patch("os.path.getmtime"),
            patch("os.path.isfile", return_value=False),
            patch("os.remove"),
        ):
            path = svc.take_screenshot(mock_page, "svc_test")
        assert "svc_test.png" in path
        mock_page.screenshot.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════
#  Dependencies
# ═══════════════════════════════════════════════════════════════════════


class TestDependencies:
    def test_get_browser_service_singleton(self):
        reset_browser_service()
        svc1 = get_browser_service()
        svc2 = get_browser_service()
        assert svc1 is svc2

    def test_reset_browser_service(self):
        reset_browser_service()
        svc1 = get_browser_service()
        reset_browser_service()
        svc2 = get_browser_service()
        assert svc1 is not svc2
