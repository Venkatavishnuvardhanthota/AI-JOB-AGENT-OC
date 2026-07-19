"""Tests for Phase 11: Browser Automation."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_password_hash
from app.main import app
from app.repositories.user import UserRepository
from app.schemas.browser_automation import (
    ApplicationFormData,
    AutomationLogListItem,
    AutomationRunRequest,
    AutomationRunResponse,
    BrowserAutomationResult,
    FormFieldValue,
    SiteConfigResponse,
)
from app.services.browser.automation_service import BrowserAutomationService
from app.services.browser.form_filler import FormFiller
from app.services.browser.site_configs import get_site_config, list_permitted_sites
from app.services.browser.types import (
    AutomationResult,
    ConsentStatus,
    SiteConfig,
    StepResult,
)

# ── Fixtures ──


@pytest_asyncio.fixture
async def test_user(session: AsyncSession):
    repo = UserRepository(session)
    user = await repo.create(
        email="phase11_test@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Phase11 Test User",
    )
    return user


@pytest_asyncio.fixture
async def auth_client(test_user, session: AsyncSession):
    from app.api.deps import get_current_user

    async def override_get_db():
        yield session

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# ── Schema Tests ──


class TestBrowserAutomationSchemas:
    def test_form_field_value(self):
        ff = FormFieldValue(selector="#name", value="John", field_type="text")
        assert ff.selector == "#name"

    def test_form_field_value_invalid_type(self):
        with pytest.raises(ValueError):
            FormFieldValue(selector="#x", value="y", field_type="invalid")

    def test_application_form_data(self):
        data = ApplicationFormData(
            url="https://example.com/apply",
            fields=[FormFieldValue(selector="#name", value="John", field_type="text")],
            resume_file_path="/path/to/resume.pdf",
        )
        assert data.url == "https://example.com/apply"

    def test_automation_run_request(self):
        req = AutomationRunRequest(
            url="https://example.com/apply",
            fields=[FormFieldValue(selector="#name", value="John", field_type="text")],
        )
        assert req.url == "https://example.com/apply"

    def test_automation_run_response(self):
        resp = AutomationRunResponse(id=uuid.uuid4(), status="running", message="Started")
        assert resp.status == "running"

    def test_site_config_response(self):
        scr = SiteConfigResponse(
            site_name="greenhouse",
            consent_status="permitted",
            url_pattern="boards.greenhouse.io",
            field_selectors=["#name"],
            supports_file_upload=True,
        )
        assert scr.consent_status == "permitted"

    def test_browser_automation_result(self):
        uid = uuid.uuid4()
        data = {
            "id": uid,
            "user_id": uuid.uuid4(),
            "url": "https://example.com",
            "status": "success",
            "steps": [],
            "screenshot_paths": [],
            "created_at": "2024-01-01T00:00:00+00:00",
        }
        result = BrowserAutomationResult(**data)
        assert result.status == "success"

    def test_automation_log_list_item(self):
        uid = uuid.uuid4()
        item = AutomationLogListItem(
            id=uid,
            url="https://example.com",
            site_name="greenhouse",
            status="success",
            created_at="2024-01-01T00:00:00+00:00",
        )
        assert item.site_name == "greenhouse"


# ── Site Config Tests ──


class TestSiteConfigs:
    def test_get_site_config_greenhouse(self):
        config = get_site_config("https://boards.greenhouse.io/acme/jobs/123")
        assert config is not None
        assert config.name == "greenhouse"
        assert config.consent_status == ConsentStatus.PERMITTED

    def test_get_site_config_lever(self):
        config = get_site_config("https://jobs.lever.co/acme/123")
        assert config is not None
        assert config.name == "lever"

    def test_get_site_config_ashby(self):
        config = get_site_config("https://jobs.ashbyhq.com/acme")
        assert config is not None
        assert config.name == "ashby"

    def test_get_site_config_unknown(self):
        config = get_site_config("https://unknown-site.com/apply")
        assert config is None

    def test_list_permitted_sites(self):
        sites = list_permitted_sites()
        assert len(sites) >= 3
        names = [s["site_name"] for s in sites]
        assert "greenhouse" in names
        assert "lever" in names
        assert "ashby" in names


# ── FormFiller Tests ──


class TestFormFiller:
    @pytest.mark.asyncio
    async def test_fill_text_field(self):
        browser = MagicMock()
        browser.fill_text = AsyncMock(return_value=True)
        filler = FormFiller(browser)
        results = await filler.fill_form([
            {"selector": "#name", "value": "John", "field_type": "text"},
        ])
        assert len(results) == 1
        assert results[0].success is True
        browser.fill_text.assert_called_once_with("#name", "John")

    @pytest.mark.asyncio
    async def test_fill_textarea(self):
        browser = MagicMock()
        browser.fill_textarea = AsyncMock(return_value=True)
        filler = FormFiller(browser)
        results = await filler.fill_form([
            {"selector": "#bio", "value": "Hello", "field_type": "textarea"},
        ])
        assert results[0].success is True

    @pytest.mark.asyncio
    async def test_fill_checkbox(self):
        browser = MagicMock()
        browser.click_checkbox = AsyncMock(return_value=True)
        filler = FormFiller(browser)
        results = await filler.fill_form([
            {"selector": "#agree", "value": "true", "field_type": "checkbox"},
        ])
        assert results[0].success is True
        browser.click_checkbox.assert_called_once_with("#agree", True)

    @pytest.mark.asyncio
    async def test_fill_dropdown(self):
        browser = MagicMock()
        browser.select_dropdown = AsyncMock(return_value=True)
        filler = FormFiller(browser)
        results = await filler.fill_form([
            {"selector": "#country", "value": "US", "field_type": "dropdown"},
        ])
        assert results[0].success is True

    @pytest.mark.asyncio
    async def test_fill_radio(self):
        browser = MagicMock()
        browser.click_radio = AsyncMock(return_value=True)
        filler = FormFiller(browser)
        results = await filler.fill_form([
            {"selector": "#option1", "value": "", "field_type": "radio"},
        ])
        assert results[0].success is True

    @pytest.mark.asyncio
    async def test_fill_unknown_type(self):
        browser = MagicMock()
        filler = FormFiller(browser)
        results = await filler.fill_form([
            {"selector": "#x", "value": "y", "field_type": "unknown"},
        ])
        assert results[0].success is False

    @pytest.mark.asyncio
    async def test_fill_failure(self):
        browser = MagicMock()
        browser.fill_text = AsyncMock(return_value=False)
        filler = FormFiller(browser)
        results = await filler.fill_form([
            {"selector": "#name", "value": "John", "field_type": "text"},
        ])
        assert results[0].success is False

    @pytest.mark.asyncio
    async def test_upload_resume(self):
        browser = MagicMock()
        browser.upload_file = AsyncMock(return_value=True)
        filler = FormFiller(browser)
        result = await filler.upload_resume("input[name='resume']", "/path/file.pdf")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_upload_cover_letter(self):
        browser = MagicMock()
        browser.upload_file = AsyncMock(return_value=True)
        filler = FormFiller(browser)
        result = await filler.upload_cover_letter("input[name='cl']", "/path/cl.pdf")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_upload_certificate(self):
        browser = MagicMock()
        browser.upload_file = AsyncMock(return_value=True)
        filler = FormFiller(browser)
        result = await filler.upload_certificate("input[name='cert']", "/path/cert.pdf")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_click_submit(self):
        browser = MagicMock()
        browser.click_submit = AsyncMock(return_value=True)
        filler = FormFiller(browser)
        result = await filler.click_submit("button[type='submit']")
        assert result.success is True


# ── BrowserAutomationService Tests ──


class TestBrowserAutomationService:
    @pytest.mark.asyncio
    async def test_run_success(self):
        session = MagicMock(spec=AsyncSession)
        session.flush = AsyncMock()
        session.add = MagicMock()

        svc = BrowserAutomationService(session)

        mock_client = MagicMock()
        mock_client.start = AsyncMock()
        mock_client.close = AsyncMock()
        mock_client.navigate = AsyncMock()
        mock_client.fill_text = AsyncMock(return_value=True)
        mock_client.fill_textarea = AsyncMock(return_value=True)
        mock_client.click_checkbox = AsyncMock(return_value=True)
        mock_client.select_dropdown = AsyncMock(return_value=True)
        mock_client.click_radio = AsyncMock(return_value=True)
        mock_client.upload_file = AsyncMock(return_value=True)
        mock_client.click_submit = AsyncMock(return_value=True)
        mock_client.take_screenshot = AsyncMock(return_value="/tmp/ss.png")
        mock_client.wait_for_selector = AsyncMock()
        mock_client.is_element_present = AsyncMock(return_value=True)
        mock_client.get_page_title = AsyncMock(return_value="Apply")
        mock_client.get_current_url = AsyncMock(return_value="https://boards.greenhouse.io/acme/jobs/123")

        with patch.object(svc, "_create_client", return_value=mock_client):
            result = await svc.run_automation(
                user_id=uuid.uuid4(),
                url="https://boards.greenhouse.io/acme/jobs/123",
                fields=[
                    {"selector": "#name", "value": "John", "field_type": "text"},
                ],
                resume_file_path="/tmp/resume.pdf",
            )

        assert result.success is True
        assert result.status == "success"
        assert len(result.steps) >= 2

    @pytest.mark.asyncio
    async def test_run_site_not_permitted(self):
        session = MagicMock(spec=AsyncSession)
        session.flush = AsyncMock()
        session.add = MagicMock()

        not_permitted_config = SiteConfig(
            name="TestBlocked",
            url_pattern=r".*",
            consent_status=ConsentStatus.NOT_PERMITTED,
            fields=[],
        )

        svc = BrowserAutomationService(session)
        with patch(
            "app.services.browser.automation_service.get_site_config",
            return_value=not_permitted_config,
        ):
            result = await svc.run_automation(
                user_id=uuid.uuid4(),
                url="https://example.com/apply",
                fields=[],
            )

        assert result.success is False
        assert result.status == "failed"
        assert "not permitted" in result.error

    @pytest.mark.asyncio
    async def test_run_navigation_failure(self):
        session = MagicMock(spec=AsyncSession)
        session.flush = AsyncMock()
        session.add = MagicMock()

        svc = BrowserAutomationService(session)

        mock_client = MagicMock()
        mock_client.start = AsyncMock()
        mock_client.close = AsyncMock()
        mock_client.navigate = AsyncMock(side_effect=Exception("Timeout"))
        mock_client.take_screenshot = AsyncMock(return_value="/tmp/ss.png")

        with patch.object(svc, "_create_client", return_value=mock_client):
            result = await svc.run_automation(
                user_id=uuid.uuid4(),
                url="https://boards.greenhouse.io/acme/jobs/123",
                fields=[],
            )

        assert result.success is False

    @pytest.mark.asyncio
    async def test_run_with_retries_then_succeed(self):
        session = MagicMock(spec=AsyncSession)
        session.flush = AsyncMock()
        session.add = MagicMock()

        svc = BrowserAutomationService(session)
        svc._max_retries = 2

        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("First attempt failed")
            return

        mock_client = MagicMock()
        mock_client.start = AsyncMock(side_effect=fail_then_succeed)
        mock_client.close = AsyncMock()
        mock_client.navigate = AsyncMock()
        mock_client.fill_text = AsyncMock(return_value=True)
        mock_client.take_screenshot = AsyncMock(return_value="/tmp/ss.png")
        mock_client.click_submit = AsyncMock(return_value=True)

        with (
            patch.object(svc, "_create_client", return_value=mock_client),
            patch.object(svc, "_sleep", AsyncMock()),
        ):
            result = await svc.run_automation(
                user_id=uuid.uuid4(),
                url="https://boards.greenhouse.io/acme/jobs/123",
                fields=[],
            )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_get_log_found(self):
        mock_log = MagicMock()
        mock_log.id = uuid.uuid4()
        mock_log.url = "https://example.com"

        session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_log)
        session.execute = AsyncMock(return_value=mock_result)

        svc = BrowserAutomationService(session)
        log = await svc.get_log(mock_log.id, uuid.uuid4())
        assert log is not None
        assert log.url == "https://example.com"

    @pytest.mark.asyncio
    async def test_get_log_not_found(self):
        session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=mock_result)

        svc = BrowserAutomationService(session)
        log = await svc.get_log(uuid.uuid4(), uuid.uuid4())
        assert log is None

    @pytest.mark.asyncio
    async def test_list_logs(self):
        mock_log = MagicMock()
        mock_log.url = "https://example.com"

        session = MagicMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalars = MagicMock(return_value=MagicMock())
        mock_result.scalars.return_value.all = MagicMock(return_value=[mock_log])
        session.execute = AsyncMock(return_value=mock_result)

        svc = BrowserAutomationService(session)
        logs = await svc.list_logs(uuid.uuid4())
        assert len(logs) == 1


# ── API Integration Tests ──


class TestPhase11APIIntegration:
    @pytest.mark.asyncio
    async def test_list_sites_endpoint(self, auth_client):
        resp = await auth_client.get("/api/v1/company/automation/sites")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        names = [s["site_name"] for s in data]
        assert "greenhouse" in names

    @pytest.mark.asyncio
    async def test_run_automation_endpoint(self, auth_client):
        with patch.object(
            BrowserAutomationService, "run_automation",
            AsyncMock(return_value=AutomationResult(
                success=True, status="success",
                steps=[StepResult(step_name="test", success=True, duration_ms=100)],
            )),
        ):
            resp = await auth_client.post(
                "/api/v1/company/automation/run",
                json={
                    "url": "https://boards.greenhouse.io/acme/jobs/123",
                    "fields": [
                        {"selector": "#name", "value": "John", "field_type": "text"},
                    ],
                },
            )

        assert resp.status_code == 202, resp.text
        data = resp.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_run_automation_without_auth(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/api/v1/company/automation/run",
                json={"url": "https://example.com", "fields": []},
            )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_logs_endpoint(self, auth_client):
        resp = await auth_client.get("/api/v1/company/automation/logs")
        assert resp.status_code == 200, resp.text

    @pytest.mark.asyncio
    async def test_get_log_not_found(self, auth_client):
        resp = await auth_client.get(
            f"/api/v1/company/automation/logs/{uuid.uuid4()}"
        )
        assert resp.status_code == 404
