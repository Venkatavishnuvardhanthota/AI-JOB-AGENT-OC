"""Tests for Phase 14: Dashboard, Statistics, Charts, Reports."""

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
from app.models.application_tracking import Application
from app.repositories.user import UserRepository
from app.schemas.dashboard import (
    ChartDataResponse,
    DashboardSummary,
    StatisticsResponse,
    StatusCount,
    TopCompany,
    TrendDataPoint,
)
from app.services.dashboard_service import ChartService, DashboardService, StatisticsService
from app.services.report_service import ReportService

# ── Fixtures ──


@pytest_asyncio.fixture
async def test_user(session: AsyncSession):
    repo = UserRepository(session)
    user = await repo.create(
        email="dashboard_test@example.com",
        hashed_password=get_password_hash("secret"),
        full_name="Dashboard Tester",
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


class TestDashboardSchemas:
    def test_status_count(self):
        sc = StatusCount(status="applied", count=5)
        assert sc.status == "applied"
        assert sc.count == 5

    def test_top_company(self):
        tc = TopCompany(company_name="Acme", count=3)
        assert tc.company_name == "Acme"
        assert tc.count == 3

    def test_trend_data_point(self):
        tdp = TrendDataPoint(date="2025-01-15", count=7)
        assert tdp.date == "2025-01-15"
        assert tdp.count == 7

    def test_dashboard_summary(self):
        ds = DashboardSummary(
            total_applications=10,
            active_applications=8,
            applications_this_week=2,
            applications_this_month=5,
            interviews_scheduled=3,
            offers_received=1,
            interview_rate=30.0,
            success_rate=10.0,
            status_breakdown=[StatusCount(status="applied", count=5)],
        )
        assert ds.total_applications == 10
        assert ds.interview_rate == 30.0
        assert len(ds.status_breakdown) == 1

    def test_statistics_response(self):
        sr = StatisticsResponse(
            period="month",
            total_applications=10,
            status_breakdown=[],
            daily_trend=[],
            weekly_trend=[],
            monthly_trend=[],
            previous_period_total=5,
            growth_percentage=100.0,
            top_companies=[],
            interview_rate=20.0,
            success_rate=10.0,
        )
        assert sr.period == "month"
        assert sr.growth_percentage == 100.0

    def test_chart_data_response(self):
        from app.schemas.dashboard import ChartDataset
        chart = ChartDataResponse(
            labels=["Applied", "Interview"],
            datasets=[ChartDataset(label="test", data=[5, 3])],
        )
        assert len(chart.labels) == 2
        assert chart.datasets[0].label == "test"


# ── Service Tests ──


class TestDashboardService:
    @pytest.mark.asyncio
    async def test_get_summary(self):
        session = MagicMock(spec=AsyncSession)
        scalar_mock = MagicMock(scalar=MagicMock(return_value=5))
        scalar_iter = MagicMock(
            __iter__=MagicMock(return_value=iter([("applied", 3), ("interview", 2)]))
        )
        session.execute = AsyncMock(side_effect=[
            scalar_mock,  # total
            scalar_mock,  # active
            scalar_mock,  # week
            scalar_mock,  # month
            scalar_mock,  # interview
            scalar_mock,  # offer
            scalar_mock,  # accepted
            scalar_iter,  # status breakdown
        ])
        svc = DashboardService(session)
        result = await svc.get_summary(uuid.uuid4())
        assert result.total_applications == 5
        assert result.interviews_scheduled == 5
        assert len(result.status_breakdown) == 2


class TestStatisticsService:
    @pytest.mark.asyncio
    async def test_get_statistics_default(self):
        session = MagicMock(spec=AsyncSession)
        scalar_mock = MagicMock(scalar=MagicMock(return_value=5))
        iter_status = MagicMock(
            __iter__=MagicMock(return_value=iter([("applied", 3), ("interview", 2)]))
        )
        iter_daily = MagicMock(
            __iter__=MagicMock(return_value=iter([("2025-01-01", 2), ("2025-01-02", 3)]))
        )
        iter_weekly = MagicMock(__iter__=MagicMock(return_value=iter([])))
        iter_monthly = MagicMock(__iter__=MagicMock(return_value=iter([])))
        iter_company = MagicMock(
            __iter__=MagicMock(return_value=iter([("Acme", 3)]))
        )
        session.execute = AsyncMock(side_effect=[
            scalar_mock,    # total
            iter_status,    # status breakdown
            iter_daily,     # daily trend
            iter_weekly,    # weekly trend
            iter_monthly,   # monthly trend
            scalar_mock,    # prev total
            iter_company,   # top companies
            scalar_mock,    # interview count
            scalar_mock,    # accepted count
        ])
        svc = StatisticsService(session)
        result = await svc.get_statistics(uuid.uuid4())
        assert result.total_applications == 5
        assert len(result.status_breakdown) == 2
        assert len(result.daily_trend) == 2


class TestChartService:
    @pytest.mark.asyncio
    async def test_get_status_distribution(self):
        session = MagicMock(spec=AsyncSession)
        iter_mock = MagicMock(
            __iter__=MagicMock(return_value=iter([("applied", 5), ("interview", 3)]))
        )
        session.execute = AsyncMock(return_value=iter_mock)
        svc = ChartService(session)
        result = await svc.get_status_distribution(uuid.uuid4())
        assert len(result.labels) == 2
        assert result.labels[0] == "applied"

    @pytest.mark.asyncio
    async def test_get_daily_trends(self):
        session = MagicMock(spec=AsyncSession)
        iter_mock = MagicMock(
            __iter__=MagicMock(return_value=iter([("2025-01-01", 2), ("2025-01-02", 3)]))
        )
        session.execute = AsyncMock(return_value=iter_mock)
        svc = ChartService(session)
        result = await svc.get_daily_trends(uuid.uuid4(), days=7)
        assert len(result.labels) == 2

    @pytest.mark.asyncio
    async def test_get_weekly_trends(self):
        session = MagicMock(spec=AsyncSession)
        iter_mock = MagicMock(
            __iter__=MagicMock(return_value=iter([("2025-W01", 2), ("2025-W02", 3)]))
        )
        session.execute = AsyncMock(return_value=iter_mock)
        svc = ChartService(session)
        result = await svc.get_weekly_trends(uuid.uuid4(), weeks=4)
        assert len(result.labels) == 2

    @pytest.mark.asyncio
    async def test_get_monthly_trends(self):
        session = MagicMock(spec=AsyncSession)
        iter_mock = MagicMock(
            __iter__=MagicMock(return_value=iter([("2025-01", 2), ("2025-02", 3)]))
        )
        session.execute = AsyncMock(return_value=iter_mock)
        svc = ChartService(session)
        result = await svc.get_monthly_trends(uuid.uuid4(), months=6)
        assert len(result.labels) == 2

    @pytest.mark.asyncio
    async def test_get_company_distribution(self):
        session = MagicMock(spec=AsyncSession)
        iter_mock = MagicMock(
            __iter__=MagicMock(return_value=iter([("Acme", 5), ("Tech", 3)]))
        )
        session.execute = AsyncMock(return_value=iter_mock)
        svc = ChartService(session)
        result = await svc.get_company_distribution(uuid.uuid4(), limit=5)
        assert len(result.labels) == 2

    @pytest.mark.asyncio
    async def test_get_funnel(self):
        session = MagicMock(spec=AsyncSession)
        scalar_mock = MagicMock(scalar=MagicMock(return_value=5))
        session.execute = AsyncMock(return_value=scalar_mock)
        svc = ChartService(session)
        result = await svc.get_funnel(uuid.uuid4())
        assert len(result.labels) == 6

    @pytest.mark.asyncio
    async def test_get_daily_statistics(self):
        session = MagicMock(spec=AsyncSession)
        scalar_mock = MagicMock(scalar=MagicMock(return_value=5))
        iter_mock = MagicMock(
            __iter__=MagicMock(return_value=iter([("applied", 3), ("interview", 2)]))
        )
        session.execute = AsyncMock(side_effect=[
            scalar_mock,  # total
            iter_mock,    # status breakdown
        ])
        svc = ChartService(session)
        result = await svc.get_daily_statistics(uuid.uuid4())
        assert result.applications_created == 5
        assert len(result.status_breakdown) == 2


class TestReportService:
    @pytest.mark.asyncio
    async def test_generate_csv_daily(self):
        session = MagicMock(spec=AsyncSession)
        mock_app = MagicMock(spec=Application)
        mock_app.id = uuid.uuid4()
        mock_app.job_title = "Engineer"
        mock_app.company_name = "Acme"
        mock_app.status = "applied"
        mock_app.location = "Remote"
        mock_app.applied_at = datetime.now(timezone.utc)
        mock_app.tag_mappings = []
        scalar_mock = MagicMock(scalar=MagicMock(return_value=5))
        iter_status = MagicMock(
            __iter__=MagicMock(return_value=iter([("applied", 3), ("interview", 2)]))
        )
        iter_company = MagicMock(
            __iter__=MagicMock(return_value=iter([("Acme", 3)]))
        )
        iter_daily = MagicMock(
            __iter__=MagicMock(return_value=iter([("2025-01-15", 5)]))
        )
        unique_mock = MagicMock()
        unique_mock.unique = MagicMock(return_value=unique_mock)
        unique_mock.scalars = MagicMock(return_value=MagicMock())
        unique_mock.scalars().all = MagicMock(return_value=[mock_app])
        session.execute = AsyncMock(side_effect=[
            unique_mock,  # _get_applications_in_range
            iter_status,  # _get_status_breakdown
            iter_company,  # _get_top_companies
            scalar_mock,  # _get_rates total
            scalar_mock,  # _get_rates interview
            scalar_mock,  # _get_rates accepted
            iter_daily,   # _get_daily_breakdown
        ])
        svc = ReportService(session)
        content, filename, media_type = await svc.generate_report(
            uuid.uuid4(), "daily", "csv",
        )
        assert filename.endswith(".csv")
        assert media_type == "text/csv"
        assert "Engineer" in content.decode("utf-8")

    @pytest.mark.asyncio
    async def test_generate_xlsx_monthly(self):
        session = MagicMock(spec=AsyncSession)
        mock_app = MagicMock(spec=Application)
        mock_app.id = uuid.uuid4()
        mock_app.job_title = "Engineer"
        mock_app.company_name = "Acme"
        mock_app.status = "applied"
        mock_app.location = "Remote"
        mock_app.applied_at = datetime.now(timezone.utc)
        mock_app.tag_mappings = []
        scalar_mock = MagicMock(scalar=MagicMock(return_value=5))
        iter_status = MagicMock(
            __iter__=MagicMock(return_value=iter([("applied", 3), ("interview", 2)]))
        )
        iter_company = MagicMock(
            __iter__=MagicMock(return_value=iter([("Acme", 3)]))
        )
        iter_daily = MagicMock(
            __iter__=MagicMock(return_value=iter([("2025-01-15", 5)]))
        )
        unique_mock = MagicMock()
        unique_mock.unique = MagicMock(return_value=unique_mock)
        unique_mock.scalars = MagicMock(return_value=MagicMock())
        unique_mock.scalars().all = MagicMock(return_value=[mock_app])
        session.execute = AsyncMock(side_effect=[
            unique_mock,  # _get_applications_in_range
            iter_status,  # _get_status_breakdown
            iter_company,  # _get_top_companies
            scalar_mock,  # _get_rates total
            scalar_mock,  # _get_rates interview
            scalar_mock,  # _get_rates accepted
            iter_daily,   # _get_daily_breakdown
        ])
        svc = ReportService(session)
        content, filename, media_type = await svc.generate_report(
            uuid.uuid4(), "monthly", "xlsx",
        )
        assert filename.endswith(".xlsx")
        assert media_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_generate_pdf_weekly(self):
        session = MagicMock(spec=AsyncSession)
        mock_app = MagicMock(spec=Application)
        mock_app.id = uuid.uuid4()
        mock_app.job_title = "Engineer"
        mock_app.company_name = "Acme"
        mock_app.status = "applied"
        mock_app.location = "Remote"
        mock_app.applied_at = datetime.now(timezone.utc)
        mock_app.tag_mappings = []
        scalar_mock = MagicMock(scalar=MagicMock(return_value=5))
        iter_status = MagicMock(
            __iter__=MagicMock(return_value=iter([("applied", 3), ("interview", 2)]))
        )
        iter_company = MagicMock(
            __iter__=MagicMock(return_value=iter([("Acme", 3)]))
        )
        iter_daily = MagicMock(
            __iter__=MagicMock(return_value=iter([("2025-01-15", 5)]))
        )
        unique_mock = MagicMock()
        unique_mock.unique = MagicMock(return_value=unique_mock)
        unique_mock.scalars = MagicMock(return_value=MagicMock())
        unique_mock.scalars().all = MagicMock(return_value=[mock_app])
        session.execute = AsyncMock(side_effect=[
            unique_mock,  # _get_applications_in_range
            iter_status,  # _get_status_breakdown
            iter_company,  # _get_top_companies
            scalar_mock,  # _get_rates total
            scalar_mock,  # _get_rates interview
            scalar_mock,  # _get_rates accepted
            iter_daily,   # _get_daily_breakdown
        ])
        svc = ReportService(session)
        content, filename, media_type = await svc.generate_report(
            uuid.uuid4(), "weekly", "pdf",
        )
        assert filename.endswith(".pdf")
        assert media_type == "application/pdf"
        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_generate_invalid_type(self):
        session = MagicMock(spec=AsyncSession)
        svc = ReportService(session)
        with pytest.raises(ValueError, match="Unsupported report type"):
            await svc.generate_report(uuid.uuid4(), "yearly", "csv")

    @pytest.mark.asyncio
    async def test_generate_invalid_format(self):
        session = MagicMock(spec=AsyncSession)
        scalar_mock = MagicMock(scalar=MagicMock(return_value=5))
        iter_mock = MagicMock(__iter__=MagicMock(return_value=iter([])))
        unique_mock = MagicMock()
        unique_mock.unique = MagicMock(return_value=unique_mock)
        unique_mock.scalars = MagicMock(return_value=MagicMock())
        unique_mock.scalars().all = MagicMock(return_value=[])
        session.execute = AsyncMock(side_effect=[
            unique_mock,
            iter_mock,
            iter_mock,
            scalar_mock,
            scalar_mock,
            scalar_mock,
            iter_mock,
        ])
        svc = ReportService(session)
        with pytest.raises(ValueError, match="Unsupported format"):
            await svc.generate_report(uuid.uuid4(), "daily", "docx")


# ── API Integration Tests ──


class TestDashboardAPIIntegration:
    @pytest.mark.asyncio
    async def test_get_dashboard_summary(self, auth_client):
        resp = await auth_client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_applications" in data
        assert "status_breakdown" in data

    @pytest.mark.asyncio
    async def test_get_statistics(self, auth_client):
        resp = await auth_client.get("/api/v1/dashboard/statistics?period=month")
        assert resp.status_code == 200
        data = resp.json()
        assert data["period"] == "month"
        assert "daily_trend" in data

    @pytest.mark.asyncio
    async def test_get_status_distribution_chart(self, auth_client):
        resp = await auth_client.get("/api/v1/dashboard/charts/status-distribution")
        assert resp.status_code == 200
        data = resp.json()
        assert "labels" in data
        assert "datasets" in data

    @pytest.mark.asyncio
    async def test_get_daily_trends_chart(self, auth_client):
        resp = await auth_client.get("/api/v1/dashboard/charts/daily-trends?days=7")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_weekly_trends_chart(self, auth_client):
        resp = await auth_client.get("/api/v1/dashboard/charts/weekly-trends?weeks=4")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_monthly_trends_chart(self, auth_client):
        resp = await auth_client.get("/api/v1/dashboard/charts/monthly-trends?months=6")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_company_distribution_chart(self, auth_client):
        resp = await auth_client.get("/api/v1/dashboard/charts/company-distribution?limit=5")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_funnel_chart(self, auth_client):
        resp = await auth_client.get("/api/v1/dashboard/charts/funnel")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_daily_statistics(self, auth_client):
        resp = await auth_client.get("/api/v1/dashboard/daily-statistics")
        assert resp.status_code == 200
        data = resp.json()
        assert "date" in data
        assert "applications_created" in data

    @pytest.mark.asyncio
    async def test_generate_csv_report(self, auth_client):
        resp = await auth_client.get("/api/v1/dashboard/reports?type=daily&format=csv")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/csv; charset=utf-8"

    @pytest.mark.asyncio
    async def test_generate_xlsx_report(self, auth_client):
        resp = await auth_client.get("/api/v1/dashboard/reports?type=weekly&format=xlsx")
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]

    @pytest.mark.asyncio
    async def test_generate_pdf_report(self, auth_client):
        resp = await auth_client.get("/api/v1/dashboard/reports?type=monthly&format=pdf")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_generate_report_invalid_type(self, auth_client):
        resp = await auth_client.get("/api/v1/dashboard/reports?type=yearly&format=csv")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_report_invalid_format(self, auth_client):
        resp = await auth_client.get("/api/v1/dashboard/reports?type=daily&format=docx")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_without_auth_returns_401(self, session):
        async def override_get_db():
            yield session

        app.dependency_overrides[get_db] = override_get_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 401
        app.dependency_overrides.clear()
