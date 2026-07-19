"""Tests for Phase 12: Manual Apply / Application Automation."""

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
from app.models.application_run import ApplicationRun
from app.models.application_schedule import ApplicationSchedule
from app.models.notification import Notification
from app.repositories.user import UserRepository
from app.schemas.application_run import ManualApplyRequest, RunListItem, RunResponse
from app.schemas.application_schedule import (
    ScheduleCreateRequest,
    ScheduleListItem,
    ScheduleResponse,
    ScheduleUpdateRequest,
)
from app.schemas.notification import (
    MarkReadRequest,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.application_automation import ApplicationAutomationService
from app.services.notification_service import NotificationService
from app.services.schedule_service import ApplicationRunService, ScheduleService

# ── Fixtures ──


@pytest_asyncio.fixture
async def test_user(session: AsyncSession):
    repo = UserRepository(session)
    user = await repo.create(
        email="apply_test@example.com",
        hashed_password=get_password_hash("secret"),
        full_name="Apply Tester",
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


class TestApplicationScheduleSchemas:
    def test_create_request_valid(self):
        req = ScheduleCreateRequest(
            name="Daily Apply",
            schedule_type="daily",
            time_of_day="09:00",
        )
        assert req.name == "Daily Apply"
        assert req.schedule_type == "daily"
        assert req.time_of_day == "09:00"
        assert req.max_applications_per_day == 10

    def test_create_request_defaults(self):
        req = ScheduleCreateRequest(
            name="Weekly Apply",
            schedule_type="weekly",
            days_of_week=[1, 3, 5],
            time_of_day="10:00",
        )
        assert req.timezone == "UTC"
        assert req.max_applications_per_day == 10

    def test_create_request_invalid_type(self):
        with pytest.raises(ValueError):
            ScheduleCreateRequest(name="Bad", schedule_type="monthly")

    def test_update_request_partial(self):
        req = ScheduleUpdateRequest(max_applications_per_day=5)
        assert req.max_applications_per_day == 5
        assert req.name is None

    def test_schedule_response_from_attrs(self):
        now = datetime.now(timezone.utc)
        resp = ScheduleResponse(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Test",
            status="active",
            schedule_type="daily",
            timezone="UTC",
            max_applications_per_day=10,
            created_at=now,
            updated_at=now,
        )
        assert resp.name == "Test"
        assert resp.status == "active"

    def test_schedule_list_item(self):
        now = datetime.now(timezone.utc)
        item = ScheduleListItem(
            id=uuid.uuid4(),
            name="Test",
            status="stopped",
            schedule_type="daily",
            max_applications_per_day=5,
            created_at=now,
        )
        assert item.name == "Test"


class TestApplicationRunSchemas:
    def test_manual_apply_request(self):
        req = ManualApplyRequest(
            job_ids=[uuid.uuid4(), uuid.uuid4()],
            max_applications=3,
        )
        assert len(req.job_ids) == 2
        assert req.max_applications == 3

    def test_run_response_from_attrs(self):
        now = datetime.now(timezone.utc)
        resp = RunResponse(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            status="completed",
            applications_submitted_count=5,
            total_jobs_target=10,
            created_at=now,
            updated_at=now,
        )
        assert resp.status == "completed"

    def test_run_list_item(self):
        now = datetime.now(timezone.utc)
        item = RunListItem(
            id=uuid.uuid4(),
            status="running",
            created_at=now,
        )
        assert item.status == "running"


class TestNotificationSchemas:
    def test_notification_response(self):
        now = datetime.now(timezone.utc)
        resp = NotificationResponse(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            type="info",
            title="Test",
            message="Hello",
            is_read=False,
            created_at=now,
            updated_at=now,
        )
        assert resp.title == "Test"
        assert resp.is_read is False

    def test_mark_read_request(self):
        nid = uuid.uuid4()
        req = MarkReadRequest(notification_ids=[nid])
        assert req.notification_ids == [nid]

    def test_unread_count_response(self):
        resp = UnreadCountResponse(count=3)
        assert resp.count == 3


# ── Schedule Service Tests ──


class TestScheduleService:
    @pytest.mark.asyncio
    async def test_create(self):
        session = MagicMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        svc = ScheduleService(session)
        schedule = await svc.create(
            user_id=uuid.uuid4(),
            name="My Schedule",
            schedule_type="daily",
            time_of_day="09:00",
        )
        assert schedule.name == "My Schedule"
        assert schedule.status == "stopped"
        assert schedule.schedule_type == "daily"
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_found(self):
        session = MagicMock(spec=AsyncSession)
        sid = uuid.uuid4()
        uid = uuid.uuid4()
        mock_schedule = MagicMock(spec=ApplicationSchedule)
        mock_schedule.id = sid
        mock_schedule.user_id = uid
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=mock_schedule)
        session.execute = AsyncMock(return_value=scalar)

        svc = ScheduleService(session)
        result = await svc.get(sid, uid)
        assert result is mock_schedule

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        session = MagicMock(spec=AsyncSession)
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=scalar)

        svc = ScheduleService(session)
        result = await svc.get(uuid.uuid4(), uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_list_by_user(self):
        session = MagicMock(spec=AsyncSession)
        mock1 = MagicMock(spec=ApplicationSchedule)
        mock2 = MagicMock(spec=ApplicationSchedule)
        scalar = MagicMock()
        scalar.scalars = MagicMock(return_value=MagicMock())
        scalar.scalars().all = MagicMock(return_value=[mock1, mock2])
        session.execute = AsyncMock(return_value=scalar)

        svc = ScheduleService(session)
        result = await svc.list_by_user(uuid.uuid4())
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_delete_found(self):
        session = MagicMock(spec=AsyncSession)
        mock_schedule = MagicMock(spec=ApplicationSchedule)
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=mock_schedule)
        session.execute = AsyncMock(return_value=scalar)
        session.delete = AsyncMock()
        session.flush = AsyncMock()

        svc = ScheduleService(session)
        result = await svc.delete(uuid.uuid4(), uuid.uuid4())
        assert result is True
        session.delete.assert_called_once_with(mock_schedule)

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        session = MagicMock(spec=AsyncSession)
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=scalar)

        svc = ScheduleService(session)
        result = await svc.delete(uuid.uuid4(), uuid.uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_start(self):
        session = MagicMock(spec=AsyncSession)
        mock_schedule = MagicMock(spec=ApplicationSchedule)
        mock_schedule.schedule_type = "daily"
        mock_schedule.time_of_day = "09:00"
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=mock_schedule)
        session.execute = AsyncMock(return_value=scalar)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        svc = ScheduleService(session)
        result = await svc.start(uuid.uuid4(), uuid.uuid4())
        assert result is mock_schedule
        assert mock_schedule.status == "active"
        assert mock_schedule.next_run_at is not None

    @pytest.mark.asyncio
    async def test_stop(self):
        session = MagicMock(spec=AsyncSession)
        mock_schedule = MagicMock(spec=ApplicationSchedule)
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=mock_schedule)
        session.execute = AsyncMock(return_value=scalar)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        svc = ScheduleService(session)
        result = await svc.stop(uuid.uuid4(), uuid.uuid4())
        assert result is mock_schedule
        assert mock_schedule.status == "stopped"

    @pytest.mark.asyncio
    async def test_pause(self):
        session = MagicMock(spec=AsyncSession)
        mock_schedule = MagicMock(spec=ApplicationSchedule)
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=mock_schedule)
        session.execute = AsyncMock(return_value=scalar)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        svc = ScheduleService(session)
        result = await svc.pause(uuid.uuid4(), uuid.uuid4())
        assert result is mock_schedule
        assert mock_schedule.status == "paused"

    @pytest.mark.asyncio
    async def test_resume(self):
        session = MagicMock(spec=AsyncSession)
        mock_schedule = MagicMock(spec=ApplicationSchedule)
        mock_schedule.schedule_type = "daily"
        mock_schedule.time_of_day = "09:00"
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=mock_schedule)
        session.execute = AsyncMock(return_value=scalar)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        svc = ScheduleService(session)
        result = await svc.resume(uuid.uuid4(), uuid.uuid4())
        assert result is mock_schedule
        assert mock_schedule.status == "active"

    @pytest.mark.asyncio
    async def test_start_not_found(self):
        session = MagicMock(spec=AsyncSession)
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=scalar)

        svc = ScheduleService(session)
        result = await svc.start(uuid.uuid4(), uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_update(self):
        session = MagicMock(spec=AsyncSession)
        mock_schedule = MagicMock(spec=ApplicationSchedule)
        mock_schedule.max_applications_per_day = 10
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=mock_schedule)
        session.execute = AsyncMock(return_value=scalar)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        svc = ScheduleService(session)
        result = await svc.update(
            uuid.uuid4(), uuid.uuid4(), max_applications_per_day=25,
        )
        assert result is mock_schedule


class TestScheduleServiceNextRun:
    def setup_schedule(self, schedule_type, **kwargs):
        s = MagicMock(spec=ApplicationSchedule)
        s.schedule_type = schedule_type
        for k, v in kwargs.items():
            setattr(s, k, v)
        return s

    def test_daily_next_run_same_day(self):
        svc = ScheduleService(MagicMock())
        schedule = self.setup_schedule("daily", time_of_day="15:00")
        from_time = datetime(2026, 7, 19, 10, 0, 0, tzinfo=timezone.utc)
        result = svc._compute_next_run(schedule, from_time)
        assert result is not None
        assert result.hour == 15
        assert result.minute == 0
        assert result.day == 19

    def test_daily_next_run_next_day(self):
        svc = ScheduleService(MagicMock())
        schedule = self.setup_schedule("daily", time_of_day="08:00")
        from_time = datetime(2026, 7, 19, 10, 0, 0, tzinfo=timezone.utc)
        result = svc._compute_next_run(schedule, from_time)
        assert result is not None
        assert result.hour == 8
        assert result.day == 20

    def test_weekly_next_run(self):
        svc = ScheduleService(MagicMock())
        schedule = self.setup_schedule(
            "weekly", days_of_week=[0, 2, 4], time_of_day="09:00",
        )
        from_time = datetime(2026, 7, 19, 10, 0, 0, tzinfo=timezone.utc)
        result = svc._compute_next_run(schedule, from_time)
        assert result is not None

    def test_custom_next_run(self):
        svc = ScheduleService(MagicMock())
        schedule = self.setup_schedule("custom", cron_expression="0 9 * * *")
        from_time = datetime(2026, 7, 19, 10, 0, 0, tzinfo=timezone.utc)
        result = svc._compute_next_run(schedule, from_time)
        assert result is not None

    def test_no_next_run_for_invalid(self):
        svc = ScheduleService(MagicMock())
        schedule = self.setup_schedule("daily", time_of_day=None)
        result = svc._compute_next_run(schedule, datetime.now(timezone.utc))
        assert result is None


# ── Application Run Service Tests ──


class TestApplicationRunService:
    @pytest.mark.asyncio
    async def test_create(self):
        session = MagicMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        svc = ApplicationRunService(session)
        run = await svc.create(
            user_id=uuid.uuid4(),
            job_ids=[uuid.uuid4()],
            total_jobs_target=1,
        )
        assert run.status == "pending"
        assert run.total_jobs_target == 1

    @pytest.mark.asyncio
    async def test_update_status(self):
        session = MagicMock(spec=AsyncSession)
        mock_run = MagicMock(spec=ApplicationRun)
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=mock_run)
        session.execute = AsyncMock(return_value=scalar)
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        svc = ApplicationRunService(session)
        result = await svc.update_status(uuid.uuid4(), "completed", 5)
        assert result is mock_run
        assert mock_run.status == "completed"
        assert mock_run.applications_submitted_count == 5

    @pytest.mark.asyncio
    async def test_update_status_not_found(self):
        session = MagicMock(spec=AsyncSession)
        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=scalar)

        svc = ApplicationRunService(session)
        result = await svc.update_status(uuid.uuid4(), "completed")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_by_user(self):
        session = MagicMock(spec=AsyncSession)
        mock_run = MagicMock(spec=ApplicationRun)
        scalar = MagicMock()
        scalar.scalars = MagicMock(return_value=MagicMock())
        scalar.scalars().all = MagicMock(return_value=[mock_run])
        session.execute = AsyncMock(return_value=scalar)

        svc = ApplicationRunService(session)
        result = await svc.list_by_user(uuid.uuid4())
        assert len(result) == 1


# ── Notification Service Tests ──


class TestNotificationService:
    @pytest.mark.asyncio
    async def test_create(self):
        session = MagicMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        svc = NotificationService(session)
        notification = await svc.create(
            user_id=uuid.uuid4(),
            notification_type="info",
            title="Test Notification",
            message="This is a test.",
        )
        assert notification.title == "Test Notification"
        assert notification.type == "info"
        assert notification.is_read is False

    @pytest.mark.asyncio
    async def test_list_by_user(self):
        session = MagicMock(spec=AsyncSession)
        mock_n = MagicMock(spec=Notification)
        scalar = MagicMock()
        scalar.scalars = MagicMock(return_value=MagicMock())
        scalar.scalars().all = MagicMock(return_value=[mock_n])
        session.execute = AsyncMock(return_value=scalar)

        svc = NotificationService(session)
        result = await svc.list_by_user(uuid.uuid4())
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_unread_only(self):
        session = MagicMock(spec=AsyncSession)
        scalar = MagicMock()
        scalar.scalars = MagicMock(return_value=MagicMock())
        scalar.scalars().all = MagicMock(return_value=[])
        session.execute = AsyncMock(return_value=scalar)

        svc = NotificationService(session)
        result = await svc.list_by_user(uuid.uuid4(), unread_only=True)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_mark_read(self):
        session = MagicMock(spec=AsyncSession)
        result_mock = MagicMock()
        result_mock.rowcount = 2
        session.execute = AsyncMock(return_value=result_mock)
        session.flush = AsyncMock()

        svc = NotificationService(session)
        count = await svc.mark_read(
            uuid.uuid4(), [uuid.uuid4(), uuid.uuid4()],
        )
        assert count == 2

    @pytest.mark.asyncio
    async def test_unread_count(self):
        session = MagicMock(spec=AsyncSession)
        scalar = MagicMock()
        scalar.scalar = MagicMock(return_value=5)
        session.execute = AsyncMock(return_value=scalar)

        svc = NotificationService(session)
        count = await svc.unread_count(uuid.uuid4())
        assert count == 5


# ── Application Automation Service Tests ──


class TestApplicationAutomationService:
    @pytest.mark.asyncio
    async def test_manual_apply(self):
        session = MagicMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        mock_run = MagicMock(spec=ApplicationRun)
        mock_run.id = uuid.uuid4()
        mock_run.user_id = uuid.uuid4()
        mock_run.status = "running"
        mock_run.applications_submitted_count = 0
        mock_run.total_jobs_target = 2

        scalar = MagicMock()
        scalar.scalar_one_or_none = MagicMock(return_value=mock_run)
        session.execute = AsyncMock(return_value=scalar)

        svc = ApplicationAutomationService(session)
        job_ids = [uuid.uuid4(), uuid.uuid4()]
        result = await svc.manual_apply(
            user_id=uuid.uuid4(),
            job_ids=job_ids,
            max_applications=2,
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_daily_stats(self):
        session = MagicMock(spec=AsyncSession)
        scalar = MagicMock()
        scalar.scalar = MagicMock(return_value=3)
        session.execute = AsyncMock(return_value=scalar)

        svc = ApplicationAutomationService(session)
        stats = await svc.get_daily_stats(uuid.uuid4())
        assert stats["applications_today"] == 3
        assert "total_runs" in stats
        assert "successful_runs" in stats

    @pytest.mark.asyncio
    async def test_count_applications_today(self):
        session = MagicMock(spec=AsyncSession)
        scalar = MagicMock()
        scalar.scalar = MagicMock(return_value=5)
        session.execute = AsyncMock(return_value=scalar)

        svc = ApplicationAutomationService(session)
        count = await svc._count_applications_today(
            uuid.uuid4(), datetime.now(timezone.utc),
        )
        assert count == 5

    @pytest.mark.asyncio
    async def test_check_and_run_due_schedules_empty(self):
        session = MagicMock(spec=AsyncSession)
        scalar = MagicMock()
        scalar.scalars = MagicMock(return_value=MagicMock())
        scalar.scalars().all = MagicMock(return_value=[])
        session.execute = AsyncMock(return_value=scalar)

        svc = ApplicationAutomationService(session)
        runs = await svc.check_and_run_due_schedules()
        assert runs == []

    @pytest.mark.asyncio
    async def test_check_and_run_due_schedules_with_schedule(self):
        session = MagicMock(spec=AsyncSession)
        mock_schedule = MagicMock(spec=ApplicationSchedule)
        mock_schedule.id = uuid.uuid4()
        mock_schedule.user_id = uuid.uuid4()
        mock_schedule.max_applications_per_day = 10
        mock_schedule.time_of_day = "09:00"
        mock_schedule.timezone = "UTC"

        scalar = MagicMock()
        scalar.scalars = MagicMock(return_value=MagicMock())
        scalar.scalars().all = MagicMock(return_value=[mock_schedule])
        session.execute = AsyncMock(return_value=scalar)
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        svc = ApplicationAutomationService(session)
        runs = await svc.check_and_run_due_schedules()
        assert len(runs) == 0


# ── API Integration Tests ──


class TestPhase12APIIntegration:
    @pytest.mark.asyncio
    async def test_create_schedule_endpoint(self, auth_client):
        resp = await auth_client.post(
            "/api/v1/apply/schedules",
            json={
                "name": "Daily Job Hunt",
                "schedule_type": "daily",
                "time_of_day": "08:00",
                "max_applications_per_day": 5,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Daily Job Hunt"
        assert data["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_list_schedules_endpoint(self, auth_client):
        await auth_client.post(
            "/api/v1/apply/schedules",
            json={"name": "S1", "schedule_type": "daily", "time_of_day": "09:00"},
        )
        resp = await auth_client.get("/api/v1/apply/schedules")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_schedule_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/apply/schedules",
            json={"name": "S2", "schedule_type": "weekly", "days_of_week": [1, 3, 5], "time_of_day": "10:00"},
        )
        sid = create_resp.json()["id"]
        resp = await auth_client.get(f"/api/v1/apply/schedules/{sid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "S2"

    @pytest.mark.asyncio
    async def test_get_schedule_not_found(self, auth_client):
        resp = await auth_client.get(f"/api/v1/apply/schedules/{uuid.uuid4()}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_schedule_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/apply/schedules",
            json={"name": "S3", "schedule_type": "daily", "time_of_day": "09:00"},
        )
        sid = create_resp.json()["id"]
        resp = await auth_client.patch(
            f"/api/v1/apply/schedules/{sid}",
            json={"max_applications_per_day": 15},
        )
        assert resp.status_code == 200
        assert resp.json()["max_applications_per_day"] == 15

    @pytest.mark.asyncio
    async def test_delete_schedule_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/apply/schedules",
            json={"name": "S4", "schedule_type": "daily", "time_of_day": "09:00"},
        )
        sid = create_resp.json()["id"]
        resp = await auth_client.delete(f"/api/v1/apply/schedules/{sid}")
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_start_schedule_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/apply/schedules",
            json={"name": "S5", "schedule_type": "daily", "time_of_day": "09:00"},
        )
        sid = create_resp.json()["id"]
        resp = await auth_client.post(f"/api/v1/apply/schedules/{sid}/start")
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    @pytest.mark.asyncio
    async def test_stop_schedule_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/apply/schedules",
            json={"name": "S6", "schedule_type": "daily", "time_of_day": "09:00"},
        )
        sid = create_resp.json()["id"]
        await auth_client.post(f"/api/v1/apply/schedules/{sid}/start")
        resp = await auth_client.post(f"/api/v1/apply/schedules/{sid}/stop")
        assert resp.status_code == 200
        assert resp.json()["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_pause_schedule_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/apply/schedules",
            json={"name": "S7", "schedule_type": "daily", "time_of_day": "09:00"},
        )
        sid = create_resp.json()["id"]
        await auth_client.post(f"/api/v1/apply/schedules/{sid}/start")
        resp = await auth_client.post(f"/api/v1/apply/schedules/{sid}/pause")
        assert resp.status_code == 200
        assert resp.json()["status"] == "paused"

    @pytest.mark.asyncio
    async def test_resume_schedule_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/apply/schedules",
            json={"name": "S8", "schedule_type": "daily", "time_of_day": "09:00"},
        )
        sid = create_resp.json()["id"]
        await auth_client.post(f"/api/v1/apply/schedules/{sid}/start")
        await auth_client.post(f"/api/v1/apply/schedules/{sid}/pause")
        resp = await auth_client.post(f"/api/v1/apply/schedules/{sid}/resume")
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    @pytest.mark.asyncio
    async def test_manual_apply_endpoint(self, auth_client):
        resp = await auth_client.post(
            "/api/v1/apply/runs",
            json={
                "job_ids": [str(uuid.uuid4())],
                "max_applications": 1,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] in ("running", "completed", "completed_with_errors")

    @pytest.mark.asyncio
    async def test_list_runs_endpoint(self, auth_client):
        await auth_client.post(
            "/api/v1/apply/runs",
            json={"job_ids": [str(uuid.uuid4())], "max_applications": 1},
        )
        resp = await auth_client.get("/api/v1/apply/runs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_run_endpoint(self, auth_client):
        create_resp = await auth_client.post(
            "/api/v1/apply/runs",
            json={"job_ids": [str(uuid.uuid4())], "max_applications": 1},
        )
        rid = create_resp.json()["id"]
        resp = await auth_client.get(f"/api/v1/apply/runs/{rid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == rid

    @pytest.mark.asyncio
    async def test_get_run_not_found(self, auth_client):
        resp = await auth_client.get(f"/api/v1/apply/runs/{uuid.uuid4()}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_notifications_endpoint(self, auth_client):
        resp = await auth_client.get("/api/v1/apply/notifications")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_unread_count_endpoint(self, auth_client):
        resp = await auth_client.get("/api/v1/apply/notifications/unread-count")
        assert resp.status_code == 200
        assert "count" in resp.json()

    @pytest.mark.asyncio
    async def test_mark_read_endpoint(self, auth_client):
        resp = await auth_client.post(
            "/api/v1/apply/notifications/mark-read",
            json={"notification_ids": []},
        )
        assert resp.status_code == 200
        assert resp.json()["marked_read"] == 0

    @pytest.mark.asyncio
    async def test_stats_endpoint(self, auth_client):
        resp = await auth_client.get("/api/v1/apply/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "applications_today" in data
        assert "total_runs" in data

    @pytest.mark.asyncio
    async def test_schedule_control_not_found(self, auth_client):
        resp = await auth_client.post(f"/api/v1/apply/schedules/{uuid.uuid4()}/start")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_manual_apply_without_auth(self, session):
        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/apply/runs",
                json={"job_ids": [str(uuid.uuid4())], "max_applications": 1},
            )
        assert resp.status_code == 401
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_schedule_without_auth(self, session):
        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/apply/schedules",
                json={"name": "Test", "schedule_type": "daily", "time_of_day": "09:00"},
            )
        assert resp.status_code == 401
        app.dependency_overrides.clear()
