"""Tests for Phase 13: Application History & Tracking."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_password_hash
from app.main import app
from app.models.application_tracking import Application, ApplicationTag, ApplicationTimelineEvent
from app.repositories.user import UserRepository
from app.schemas.application_tracking import (
    ApplicationAnalytics,
    ApplicationCreateRequest,
    ApplicationListItem,
    ApplicationResponse,
    ApplicationUpdateRequest,
    NoteCreateRequest,
    NoteResponse,
    StatusCount,
    TagCreateRequest,
    TagResponse,
    TagUpdateRequest,
    TimelineEventResponse,
    TopCompany,
)
from app.services.application_tracking import (
    ApplicationAnalyticsService,
    ApplicationExportService,
    ApplicationTrackingService,
)

# ── Fixtures ──


@pytest_asyncio.fixture
async def test_user(session: AsyncSession):
    repo = UserRepository(session)
    user = await repo.create(
        email="tracking_test@example.com",
        hashed_password=get_password_hash("secret"),
        full_name="Tracking Tester",
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


class TestApplicationSchemas:
    def test_create_request_valid(self):
        req = ApplicationCreateRequest(
            job_posting_id=uuid.uuid4(),
            job_title="Software Engineer",
            company_name="Acme Corp",
            status="applied",
        )
        assert req.job_title == "Software Engineer"
        assert req.status == "applied"

    def test_create_request_defaults(self):
        req = ApplicationCreateRequest(
            job_posting_id=uuid.uuid4(),
            job_title="Engineer",
            company_name="Acme",
        )
        assert req.status == "saved"
        assert req.tag_ids == []

    def test_update_request_partial(self):
        req = ApplicationUpdateRequest(status="interview")
        assert req.status == "interview"
        assert req.job_title is None

    def test_application_response_from_attrs(self):
        now = datetime.now(timezone.utc)
        resp = ApplicationResponse(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            status="applied",
            job_title="Engineer",
            company_name="Acme",
            created_at=now,
            updated_at=now,
        )
        assert resp.status == "applied"
        assert resp.tags == []

    def test_application_list_item(self):
        now = datetime.now(timezone.utc)
        item = ApplicationListItem(
            id=uuid.uuid4(),
            status="saved",
            job_title="Dev",
            company_name="Co",
            created_at=now,
        )
        assert item.job_title == "Dev"

    def test_note_schemas(self):
        req = NoteCreateRequest(content="Great opportunity")
        assert req.content == "Great opportunity"
        now = datetime.now(timezone.utc)
        resp = NoteResponse(
            id=uuid.uuid4(),
            application_id=uuid.uuid4(),
            content="Note",
            created_at=now,
            updated_at=now,
        )
        assert resp.content == "Note"

    def test_tag_schemas(self):
        req = TagCreateRequest(name="priority", color="#FF0000")
        assert req.name == "priority"
        now = datetime.now(timezone.utc)
        resp = TagResponse(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="priority",
            created_at=now,
            updated_at=now,
        )
        assert resp.name == "priority"

    def test_tag_update_request(self):
        req = TagUpdateRequest(name="high-priority")
        assert req.name == "high-priority"

    def test_timeline_event_response(self):
        now = datetime.now(timezone.utc)
        resp = TimelineEventResponse(
            id=uuid.uuid4(),
            application_id=uuid.uuid4(),
            event_type="status_change",
            description="Changed to interview",
            occurred_at=now,
            created_at=now,
        )
        assert resp.event_type == "status_change"

    def test_analytics_schema(self):
        analytics = ApplicationAnalytics(
            total_applications=10,
            status_breakdown=[StatusCount(status="applied", count=5)],
            top_companies=[TopCompany(company_name="Acme", count=3)],
            applications_this_week=2,
            applications_this_month=8,
            active_applications=7,
            interview_rate=30.0,
            success_rate=10.0,
        )
        assert analytics.total_applications == 10
        assert analytics.interview_rate == 30.0


# ── Service Tests ──


class TestApplicationTrackingService:
    @pytest.mark.asyncio
    async def test_create(self):
        session = MagicMock(spec=AsyncSession)
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=scalar)
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        svc = ApplicationTrackingService(session)
        app = await svc.create(
            user_id=uuid.uuid4(),
            job_posting_id=uuid.uuid4(),
            job_title="Engineer",
            company_name="Acme",
        )
        assert app.job_title == "Engineer"
        assert app.status == "saved"

    @pytest.mark.asyncio
    async def test_create_duplicate_raises(self):
        session = MagicMock(spec=AsyncSession)
        existing = MagicMock(spec=Application)
        existing.id = uuid.uuid4()
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=existing)
        session.execute = AsyncMock(return_value=scalar)
        svc = ApplicationTrackingService(session)
        with pytest.raises(ValueError, match="Already applied"):
            await svc.create(
                user_id=uuid.uuid4(),
                job_posting_id=uuid.uuid4(),
                job_title="Engineer",
                company_name="Acme",
            )

    @pytest.mark.asyncio
    async def test_check_duplicate_found(self):
        session = MagicMock(spec=AsyncSession)
        existing = MagicMock(spec=Application)
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=existing)
        session.execute = AsyncMock(return_value=scalar)
        svc = ApplicationTrackingService(session)
        result = await svc.check_duplicate(uuid.uuid4(), uuid.uuid4())
        assert result is existing

    @pytest.mark.asyncio
    async def test_check_duplicate_not_found(self):
        session = MagicMock(spec=AsyncSession)
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=scalar)
        svc = ApplicationTrackingService(session)
        result = await svc.check_duplicate(uuid.uuid4(), uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_update_status(self):
        session = MagicMock(spec=AsyncSession)
        mock_app = MagicMock(spec=Application)
        mock_app.status = "saved"
        mock_app.id = uuid.uuid4()
        mock_app.user_id = uuid.uuid4()
        mock_app.job_posting_id = uuid.uuid4()
        mock_app.applied_at = None
        mock_app.notes = []
        mock_app.tag_mappings = []
        mock_app.timeline_events = []
        scalar = MagicMock()
        scalar.unique = MagicMock(return_value=scalar)
        scalar.scalar_one_or_none = MagicMock(return_value=mock_app)
        scalar.scalars = MagicMock(return_value=MagicMock())
        scalar.scalars().all = MagicMock(return_value=[])
        session.execute = AsyncMock(return_value=scalar)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        svc = ApplicationTrackingService(session)
        result = await svc.update(uuid.uuid4(), uuid.uuid4(), status="interview")
        assert result is mock_app
        assert mock_app.status == "interview"

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        session = MagicMock(spec=AsyncSession)
        scalar = MagicMock()
        scalar.unique = MagicMock(return_value=scalar)
        scalar.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=scalar)
        svc = ApplicationTrackingService(session)
        result = await svc.update(uuid.uuid4(), uuid.uuid4(), status="interview")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_found(self):
        session = MagicMock(spec=AsyncSession)
        mock_app = MagicMock(spec=Application)
        scalar = MagicMock()
        scalar.unique = MagicMock(return_value=scalar)
        scalar.scalar_one_or_none = MagicMock(return_value=mock_app)
        scalar.scalars = MagicMock(return_value=MagicMock())
        scalar.scalars().all = MagicMock(return_value=[])
        session.execute = AsyncMock(return_value=scalar)
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        svc = ApplicationTrackingService(session)
        result = await svc.delete(uuid.uuid4(), uuid.uuid4())
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        session = MagicMock(spec=AsyncSession)
        scalar = MagicMock()
        scalar.unique = MagicMock(return_value=scalar)
        scalar.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=scalar)
        svc = ApplicationTrackingService(session)
        result = await svc.delete(uuid.uuid4(), uuid.uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_add_note(self):
        session = MagicMock(spec=AsyncSession)
        mock_app = MagicMock(spec=Application)
        mock_app.id = uuid.uuid4()
        mock_app.notes = []
        mock_app.tag_mappings = []
        mock_app.timeline_events = []
        scalar = MagicMock()
        scalar.unique = MagicMock(return_value=scalar)
        scalar.scalar_one_or_none = MagicMock(return_value=mock_app)
        scalar.scalars = MagicMock(return_value=MagicMock())
        scalar.scalars().all = MagicMock(return_value=[])
        session.execute = AsyncMock(return_value=scalar)
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        svc = ApplicationTrackingService(session)
        result = await svc.add_note(uuid.uuid4(), uuid.uuid4(), "New note")
        assert result is not None
        assert result.content == "New note"

    @pytest.mark.asyncio
    async def test_create_tag(self):
        session = MagicMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        svc = ApplicationTrackingService(session)
        tag = await svc.create_tag(uuid.uuid4(), "priority", "#FF0000")
        assert tag.name == "priority"
        assert tag.color == "#FF0000"

    @pytest.mark.asyncio
    async def test_list_tags(self):
        session = MagicMock(spec=AsyncSession)
        mock_tag = MagicMock(spec=ApplicationTag)
        scalar = MagicMock()
        scalar.scalars = MagicMock(return_value=MagicMock())
        scalar.scalars().all = MagicMock(return_value=[mock_tag])
        session.execute = AsyncMock(return_value=scalar)
        svc = ApplicationTrackingService(session)
        result = await svc.list_tags(uuid.uuid4())
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_delete_tag(self):
        session = MagicMock(spec=AsyncSession)
        mock_tag = MagicMock(spec=ApplicationTag)
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=mock_tag)
        session.execute = AsyncMock(return_value=scalar)
        session.delete = AsyncMock()
        session.flush = AsyncMock()
        svc = ApplicationTrackingService(session)
        result = await svc.delete_tag(uuid.uuid4(), uuid.uuid4())
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_tag_not_found(self):
        session = MagicMock(spec=AsyncSession)
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=scalar)
        svc = ApplicationTrackingService(session)
        result = await svc.delete_tag(uuid.uuid4(), uuid.uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_add_tag_to_application(self):
        session = MagicMock(spec=AsyncSession)
        mock_app = MagicMock(spec=Application)
        mock_app.id = uuid.uuid4()
        mock_app.notes = []
        mock_app.tag_mappings = []
        mock_app.timeline_events = []
        scalar = MagicMock()
        scalar.unique = MagicMock(return_value=scalar)
        scalar.scalar_one_or_none = MagicMock(side_effect=[mock_app, None])
        scalar.scalars = MagicMock(return_value=MagicMock())
        scalar.scalars().all = MagicMock(return_value=[])
        session.execute = AsyncMock(return_value=scalar)
        session.add = MagicMock()
        session.flush = AsyncMock()
        svc = ApplicationTrackingService(session)
        result = await svc.add_tag_to_application(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
        assert result is True

    @pytest.mark.asyncio
    async def test_get_timeline(self):
        session = MagicMock(spec=AsyncSession)
        mock_event = MagicMock(spec=ApplicationTimelineEvent)
        scalar = MagicMock()
        scalar.scalars = MagicMock(return_value=MagicMock())
        scalar.scalars().all = MagicMock(return_value=[mock_event])
        session.execute = AsyncMock(return_value=scalar)
        svc = ApplicationTrackingService(session)
        result = await svc.get_timeline(uuid.uuid4(), uuid.uuid4())
        assert len(result) == 1


class TestApplicationAnalyticsService:
    @pytest.mark.asyncio
    async def test_get_analytics(self):
        session = MagicMock(spec=AsyncSession)
        scalar_call = MagicMock(scalar=MagicMock(return_value=5))
        iter_status = MagicMock(__iter__=MagicMock(return_value=iter([("applied", 3), ("interview", 2)])))
        iter_company = MagicMock(__iter__=MagicMock(return_value=iter([("Acme", 3)])))
        session.execute = AsyncMock(side_effect=[
            scalar_call,   # total
            iter_status,   # status breakdown
            iter_company,  # top companies
            scalar_call,   # week
            scalar_call,   # month
            scalar_call,   # active
            scalar_call,   # interview
            scalar_call,   # accepted
        ])
        svc = ApplicationAnalyticsService(session)
        result = await svc.get_analytics(uuid.uuid4())
        assert result["total_applications"] == 5
        assert len(result["status_breakdown"]) == 2


class TestApplicationExportService:
    @pytest.mark.asyncio
    async def test_export_csv(self):
        session = MagicMock(spec=AsyncSession)
        mock_app = MagicMock(spec=Application)
        mock_app.id = uuid.uuid4()
        mock_app.job_title = "Engineer"
        mock_app.company_name = "Acme"
        mock_app.status = "applied"
        mock_app.location = "Remote"
        mock_app.salary_range = None
        mock_app.job_url = None
        mock_app.applied_at = datetime.now(timezone.utc)
        mock_app.created_at = datetime.now(timezone.utc)
        mock_app.is_active = True
        mock_app.tag_mappings = []
        scalar = MagicMock()
        scalar.unique = MagicMock(return_value=scalar)
        scalar.scalars = MagicMock(return_value=MagicMock())
        scalar.scalars().all = MagicMock(return_value=[mock_app])
        session.execute = AsyncMock(return_value=scalar)
        svc = ApplicationExportService(session)
        csv_content = await svc.export_csv(uuid.uuid4())
        assert "Engineer" in csv_content
        assert "Acme" in csv_content
        assert csv_content.startswith("ID")


# ── API Integration Tests ──


class TestPhase13APIIntegration:
    @pytest.mark.asyncio
    async def test_create_application_endpoint(self, auth_client):
        resp = await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": str(uuid.uuid4()),
                "job_title": "Software Engineer",
                "company_name": "Acme Corp",
                "status": "applied",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["job_title"] == "Software Engineer"
        assert data["status"] == "applied"

    @pytest.mark.asyncio
    async def test_list_applications_endpoint(self, auth_client):
        await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": str(uuid.uuid4()),
                "job_title": "Engineer",
                "company_name": "Acme",
            },
        )
        resp = await auth_client.get("/api/v1/applications")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_get_application_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": str(uuid.uuid4()),
                "job_title": "Dev",
                "company_name": "Co",
            },
        )
        aid = create_resp.json()["id"]
        resp = await auth_client.get(f"/api/v1/applications/{aid}")
        assert resp.status_code == 200
        assert resp.json()["job_title"] == "Dev"

    @pytest.mark.asyncio
    async def test_get_application_not_found(self, auth_client):
        resp = await auth_client.get(f"/api/v1/applications/{uuid.uuid4()}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_application_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": str(uuid.uuid4()),
                "job_title": "Dev",
                "company_name": "Co",
            },
        )
        aid = create_resp.json()["id"]
        resp = await auth_client.patch(
            f"/api/v1/applications/{aid}",
            json={"status": "interview"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "interview"

    @pytest.mark.asyncio
    async def test_delete_application_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": str(uuid.uuid4()),
                "job_title": "Dev",
                "company_name": "Co",
            },
        )
        aid = create_resp.json()["id"]
        resp = await auth_client.delete(f"/api/v1/applications/{aid}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_check_duplicate_endpoint(self, auth_client):
        jid = str(uuid.uuid4())
        await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": jid,
                "job_title": "Dev",
                "company_name": "Co",
            },
        )
        resp = await auth_client.get(f"/api/v1/applications/check-duplicate/{jid}")
        assert resp.status_code == 200
        assert resp.json()["is_duplicate"] is True

    @pytest.mark.asyncio
    async def test_add_note_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": str(uuid.uuid4()),
                "job_title": "Dev",
                "company_name": "Co",
            },
        )
        aid = create_resp.json()["id"]
        resp = await auth_client.post(
            f"/api/v1/applications/{aid}/notes",
            json={"content": "Great company"},
        )
        assert resp.status_code == 201
        assert resp.json()["content"] == "Great company"

    @pytest.mark.asyncio
    async def test_list_notes_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": str(uuid.uuid4()),
                "job_title": "Dev",
                "company_name": "Co",
            },
        )
        aid = create_resp.json()["id"]
        await auth_client.post(f"/api/v1/applications/{aid}/notes", json={"content": "Note 1"})
        resp = await auth_client.get(f"/api/v1/applications/{aid}/notes")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_create_tag_endpoint(self, auth_client):
        resp = await auth_client.post(
            "/api/v1/applications/tags",
            json={"name": "priority", "color": "#FF0000"},
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "priority"

    @pytest.mark.asyncio
    async def test_list_tags_endpoint(self, auth_client):
        await auth_client.post(
            "/api/v1/applications/tags",
            json={"name": "urgent"},
        )
        resp = await auth_client.get("/api/v1/applications/tags")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_update_tag_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/applications/tags",
            json={"name": "old-name"},
        )
        tid = create_resp.json()["id"]
        resp = await auth_client.patch(
            f"/api/v1/applications/tags/{tid}",
            json={"name": "new-name"},
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "new-name"

    @pytest.mark.asyncio
    async def test_delete_tag_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/applications/tags",
            json={"name": "temp-tag"},
        )
        tid = create_resp.json()["id"]
        resp = await auth_client.delete(f"/api/v1/applications/tags/{tid}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_add_tag_to_application_endpoint(self, auth_client):
        app_resp = await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": str(uuid.uuid4()),
                "job_title": "Dev",
                "company_name": "Co",
            },
        )
        aid = app_resp.json()["id"]
        tag_resp = await auth_client.post(
            "/api/v1/applications/tags",
            json={"name": "test-tag"},
        )
        tid = tag_resp.json()["id"]
        resp = await auth_client.post(f"/api/v1/applications/{aid}/tags/{tid}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_remove_tag_from_application_endpoint(self, auth_client):
        app_resp = await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": str(uuid.uuid4()),
                "job_title": "Dev",
                "company_name": "Co",
            },
        )
        aid = app_resp.json()["id"]
        tag_resp = await auth_client.post(
            "/api/v1/applications/tags",
            json={"name": "remove-tag"},
        )
        tid = tag_resp.json()["id"]
        await auth_client.post(f"/api/v1/applications/{aid}/tags/{tid}")
        resp = await auth_client.delete(f"/api/v1/applications/{aid}/tags/{tid}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_timeline_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": str(uuid.uuid4()),
                "job_title": "Dev",
                "company_name": "Co",
            },
        )
        aid = create_resp.json()["id"]
        resp = await auth_client.get(f"/api/v1/applications/{aid}/timeline")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_analytics_endpoint(self, auth_client):
        await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": str(uuid.uuid4()),
                "job_title": "Engineer",
                "company_name": "Acme",
            },
        )
        resp = await auth_client.get("/api/v1/applications/analytics/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_applications"] >= 1
        assert "status_breakdown" in data

    @pytest.mark.asyncio
    async def test_export_csv_endpoint(self, auth_client):
        await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": str(uuid.uuid4()),
                "job_title": "Engineer",
                "company_name": "Acme",
            },
        )
        resp = await auth_client.get("/api/v1/applications/export/csv")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/csv; charset=utf-8"
        assert "Engineer" in resp.text

    @pytest.mark.asyncio
    async def test_filter_by_status_endpoint(self, auth_client):
        await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": str(uuid.uuid4()),
                "job_title": "Engineer",
                "company_name": "Acme",
                "status": "applied",
            },
        )
        resp = await auth_client.get("/api/v1/applications?status=applied")
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["status"] == "applied" for item in data["items"])

    @pytest.mark.asyncio
    async def test_search_endpoint(self, auth_client):
        await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": str(uuid.uuid4()),
                "job_title": "Senior Developer",
                "company_name": "Tech Inc",
            },
        )
        resp = await auth_client.get("/api/v1/applications?search=Senior")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_create_duplicate_returns_409(self, auth_client):
        jid = str(uuid.uuid4())
        await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": jid,
                "job_title": "Engineer",
                "company_name": "Acme",
            },
        )
        resp = await auth_client.post(
            "/api/v1/applications",
            json={
                "job_posting_id": jid,
                "job_title": "Engineer",
                "company_name": "Acme",
            },
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_without_auth_returns_401(self, session):
        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/applications")
        assert resp.status_code == 401
        app.dependency_overrides.clear()
