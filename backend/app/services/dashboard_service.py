import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application_tracking import Application
from app.schemas.dashboard import (
    ChartDataResponse,
    ChartDataset,
    DailyStatistics,
    DashboardSummary,
    StatisticsResponse,
    StatusCount,
    TopCompany,
    TrendDataPoint,
)

logger = logging.getLogger(__name__)


def _date_trunc_expr(column, date_part: str, session: AsyncSession):
    try:
        dialect = session.bind.dialect.name if session.bind else "postgresql"
    except Exception:
        dialect = "postgresql"
    if date_part == "day":
        return func.date(column)
    if date_part == "week":
        if dialect == "sqlite":
            return func.strftime("%Y-%W", column)
        return func.date_trunc("week", column)
    if date_part == "month":
        if dialect == "sqlite":
            return func.strftime("%Y-%m", column)
        return func.date_trunc("month", column)
    return func.date(column)


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_summary(self, user_id: uuid.UUID) -> DashboardSummary:
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)

        total = await self.session.execute(
            select(func.count(Application.id)).where(Application.user_id == user_id)
        )
        total_count = total.scalar() or 0

        active = await self.session.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id, Application.is_active == True
            )
        )
        active_count = active.scalar() or 0

        week = await self.session.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.created_at >= week_start,
            )
        )
        week_count = week.scalar() or 0

        month = await self.session.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.created_at >= month_start,
            )
        )
        month_count = month.scalar() or 0

        interview = await self.session.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.status.in_(["interview", "offer", "accepted"]),
            )
        )
        interview_count = interview.scalar() or 0

        offer = await self.session.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.status.in_(["offer", "accepted"]),
            )
        )
        offer_count = offer.scalar() or 0

        accepted = await self.session.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.status == "accepted",
            )
        )
        accepted_count = accepted.scalar() or 0

        status_result = await self.session.execute(
            select(Application.status, func.count(Application.id).label("cnt"))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
        )
        status_breakdown = [
            StatusCount(status=row[0], count=row[1]) for row in status_result
        ]

        interview_rate = round((interview_count / total_count * 100), 1) if total_count > 0 else 0.0
        success_rate = round((accepted_count / total_count * 100), 1) if total_count > 0 else 0.0

        return DashboardSummary(
            total_applications=total_count,
            active_applications=active_count,
            applications_this_week=week_count,
            applications_this_month=month_count,
            interviews_scheduled=interview_count,
            offers_received=offer_count,
            interview_rate=interview_rate,
            success_rate=success_rate,
            status_breakdown=status_breakdown,
        )


class StatisticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_statistics(
        self,
        user_id: uuid.UUID,
        period: str = "month",
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> StatisticsResponse:
        now = datetime.now(timezone.utc)
        if period == "week":
            period_start = now - timedelta(days=7)
            prev_period_start = period_start - timedelta(days=7)
        elif period == "year":
            period_start = now - timedelta(days=365)
            prev_period_start = period_start - timedelta(days=365)
        else:
            period_start = now - timedelta(days=30)
            prev_period_start = period_start - timedelta(days=30)

        if from_date:
            period_start = from_date
        period_end = to_date if to_date else now

        total = await self.session.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.created_at >= period_start,
                Application.created_at <= period_end,
            )
        )
        total_count = total.scalar() or 0

        status_result = await self.session.execute(
            select(Application.status, func.count(Application.id).label("cnt"))
            .where(
                Application.user_id == user_id,
                Application.created_at >= period_start,
                Application.created_at <= period_end,
            )
            .group_by(Application.status)
        )
        status_breakdown = [
            StatusCount(status=row[0], count=row[1]) for row in status_result
        ]

        daily_trend = await self._compute_trend(
            user_id, period_start, period_end, "day"
        )
        weekly_trend = await self._compute_trend(
            user_id, period_start, period_end, "week"
        )
        monthly_trend = await self._compute_trend(
            user_id, period_start, period_end, "month"
        )

        prev_total_result = await self.session.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.created_at >= prev_period_start,
                Application.created_at < period_start,
            )
        )
        prev_total = prev_total_result.scalar() or 0

        growth = round((total_count - prev_total) / prev_total * 100, 1) if prev_total > 0 else None

        company_result = await self.session.execute(
            select(Application.company_name, func.count(Application.id).label("cnt"))
            .where(
                Application.user_id == user_id,
                Application.created_at >= period_start,
                Application.created_at <= period_end,
            )
            .group_by(Application.company_name)
            .order_by(func.count(Application.id).desc())
            .limit(10)
        )
        top_companies = [
            TopCompany(company_name=row[0], count=row[1]) for row in company_result
        ]

        interview = await self.session.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.status.in_(["interview", "offer", "accepted"]),
                Application.created_at >= period_start,
                Application.created_at <= period_end,
            )
        )
        interview_count = interview.scalar() or 0

        accepted = await self.session.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.status == "accepted",
                Application.created_at >= period_start,
                Application.created_at <= period_end,
            )
        )
        accepted_count = accepted.scalar() or 0

        interview_rate = round((interview_count / total_count * 100), 1) if total_count > 0 else 0.0
        success_rate = round((accepted_count / total_count * 100), 1) if total_count > 0 else 0.0

        return StatisticsResponse(
            period=period,
            from_date=period_start,
            to_date=period_end,
            total_applications=total_count,
            status_breakdown=status_breakdown,
            daily_trend=daily_trend,
            weekly_trend=weekly_trend,
            monthly_trend=monthly_trend,
            previous_period_total=prev_total,
            growth_percentage=growth,
            top_companies=top_companies,
            interview_rate=interview_rate,
            success_rate=success_rate,
        )

    async def _compute_trend(
        self,
        user_id: uuid.UUID,
        start: datetime,
        end: datetime,
        date_part: str,
    ) -> list[TrendDataPoint]:
        trunc = _date_trunc_expr(Application.created_at, date_part, self.session)
        rows = await self.session.execute(
            select(trunc.label("period"), func.count(Application.id).label("cnt"))
            .where(
                Application.user_id == user_id,
                Application.created_at >= start,
                Application.created_at <= end,
            )
            .group_by(trunc)
            .order_by(trunc)
        )
        return [TrendDataPoint(date=str(row[0]), count=row[1]) for row in rows]


class ChartService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_status_distribution(self, user_id: uuid.UUID) -> ChartDataResponse:
        result = await self.session.execute(
            select(Application.status, func.count(Application.id).label("cnt"))
            .where(Application.user_id == user_id)
            .group_by(Application.status)
            .order_by(func.count(Application.id).desc())
        )
        labels = []
        data = []
        colors = {
            "saved": "#6B7280",
            "applied": "#3B82F6",
            "phone_screening": "#8B5CF6",
            "interview": "#F59E0B",
            "offer": "#10B981",
            "accepted": "#059669",
            "rejected": "#EF4444",
            "withdrawn": "#9CA3AF",
        }
        bg_colors = []
        for row in result:
            labels.append(row[0])
            data.append(row[1])
            bg_colors.append(colors.get(row[0], "#6B7280"))
        return ChartDataResponse(
            labels=labels,
            datasets=[
                ChartDataset(
                    label="Applications",
                    data=data,
                    backgroundColor=bg_colors,
                )
            ],
        )

    async def get_daily_trends(
        self, user_id: uuid.UUID, days: int = 30
    ) -> ChartDataResponse:
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days)
        trunc = _date_trunc_expr(Application.created_at, "day", self.session)
        result = await self.session.execute(
            select(trunc.label("d"), func.count(Application.id).label("cnt"))
            .where(
                Application.user_id == user_id,
                Application.created_at >= start,
            )
            .group_by(trunc)
            .order_by(trunc)
        )
        labels = []
        data = []
        for row in result:
            labels.append(str(row[0]))
            data.append(row[1])
        return ChartDataResponse(
            labels=labels,
            datasets=[
                ChartDataset(
                    label="Applications per Day",
                    data=data,
                    borderColor="#3B82F6",
                )
            ],
        )

    async def get_weekly_trends(
        self, user_id: uuid.UUID, weeks: int = 12
    ) -> ChartDataResponse:
        now = datetime.now(timezone.utc)
        start = now - timedelta(weeks=weeks)
        trunc = _date_trunc_expr(Application.created_at, "week", self.session)
        result = await self.session.execute(
            select(trunc.label("w"), func.count(Application.id).label("cnt"))
            .where(
                Application.user_id == user_id,
                Application.created_at >= start,
            )
            .group_by(trunc)
            .order_by(trunc)
        )
        labels = []
        data = []
        for row in result:
            labels.append(str(row[0]))
            data.append(row[1])
        return ChartDataResponse(
            labels=labels,
            datasets=[
                ChartDataset(
                    label="Applications per Week",
                    data=data,
                    borderColor="#8B5CF6",
                )
            ],
        )

    async def get_monthly_trends(
        self, user_id: uuid.UUID, months: int = 12
    ) -> ChartDataResponse:
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=30 * months)
        trunc = _date_trunc_expr(Application.created_at, "month", self.session)
        result = await self.session.execute(
            select(trunc.label("m"), func.count(Application.id).label("cnt"))
            .where(
                Application.user_id == user_id,
                Application.created_at >= start,
            )
            .group_by(trunc)
            .order_by(trunc)
        )
        labels = []
        data = []
        for row in result:
            labels.append(str(row[0]))
            data.append(row[1])
        return ChartDataResponse(
            labels=labels,
            datasets=[
                ChartDataset(
                    label="Applications per Month",
                    data=data,
                    borderColor="#10B981",
                )
            ],
        )

    async def get_company_distribution(
        self, user_id: uuid.UUID, limit: int = 10
    ) -> ChartDataResponse:
        result = await self.session.execute(
            select(Application.company_name, func.count(Application.id).label("cnt"))
            .where(Application.user_id == user_id)
            .group_by(Application.company_name)
            .order_by(func.count(Application.id).desc())
            .limit(limit)
        )
        labels = []
        data = []
        for row in result:
            labels.append(row[0])
            data.append(row[1])
        return ChartDataResponse(
            labels=labels,
            datasets=[
                ChartDataset(
                    label="Top Companies",
                    data=data,
                    backgroundColor=["#3B82F6", "#8B5CF6", "#F59E0B", "#10B981", "#EF4444"],
                )
            ],
        )

    async def get_funnel(self, user_id: uuid.UUID) -> ChartDataResponse:
        stages = ["saved", "applied", "phone_screening", "interview", "offer", "accepted"]
        labels = ["Saved", "Applied", "Phone Screening", "Interview", "Offer", "Accepted"]
        data = []
        for stage in stages:
            result = await self.session.execute(
                select(func.count(Application.id)).where(
                    Application.user_id == user_id,
                    Application.status == stage,
                )
            )
            data.append(result.scalar() or 0)
        return ChartDataResponse(
            labels=labels,
            datasets=[
                ChartDataset(
                    label="Application Funnel",
                    data=data,
                    backgroundColor=[
                        "#6B7280", "#3B82F6", "#8B5CF6",
                        "#F59E0B", "#10B981", "#059669",
                    ],
                )
            ],
        )

    async def get_daily_statistics(
        self, user_id: uuid.UUID, date: str | None = None
    ) -> DailyStatistics:
        now = datetime.now(timezone.utc)
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            target_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_start = target_date
        day_end = target_date + timedelta(days=1)

        total = await self.session.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.created_at >= day_start,
                Application.created_at < day_end,
            )
        )
        total_count = total.scalar() or 0

        status_result = await self.session.execute(
            select(Application.status, func.count(Application.id).label("cnt"))
            .where(
                Application.user_id == user_id,
                Application.created_at >= day_start,
                Application.created_at < day_end,
            )
            .group_by(Application.status)
        )
        status_breakdown = [
            StatusCount(status=row[0], count=row[1]) for row in status_result
        ]

        return DailyStatistics(
            date=target_date.strftime("%Y-%m-%d"),
            applications_created=total_count,
            status_breakdown=status_breakdown,
        )
