import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.dashboard import (
    ChartDataResponse,
    DailyStatistics,
    DashboardSummary,
    StatisticsResponse,
)
from app.services.dashboard_service import ChartService, DashboardService, StatisticsService
from app.services.report_service import ReportService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(db)


def get_statistics_service(db: AsyncSession = Depends(get_db)) -> StatisticsService:
    return StatisticsService(db)


def get_chart_service(db: AsyncSession = Depends(get_db)) -> ChartService:
    return ChartService(db)


def get_report_service(db: AsyncSession = Depends(get_db)) -> ReportService:
    return ReportService(db)


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardSummary:
    return await service.get_summary(current_user.id)


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    period: str = Query("month", pattern="^(week|month|year)$"),
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    service: StatisticsService = Depends(get_statistics_service),
) -> StatisticsResponse:
    from datetime import datetime, timezone
    parsed_from = None
    parsed_to = None
    if from_date:
        parsed_from = datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    if to_date:
        parsed_to = datetime.strptime(to_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return await service.get_statistics(current_user.id, period, parsed_from, parsed_to)


@router.get("/charts/status-distribution", response_model=ChartDataResponse)
async def get_status_distribution_chart(
    current_user: User = Depends(get_current_user),
    service: ChartService = Depends(get_chart_service),
) -> ChartDataResponse:
    return await service.get_status_distribution(current_user.id)


@router.get("/charts/daily-trends", response_model=ChartDataResponse)
async def get_daily_trends_chart(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    service: ChartService = Depends(get_chart_service),
) -> ChartDataResponse:
    return await service.get_daily_trends(current_user.id, days)


@router.get("/charts/weekly-trends", response_model=ChartDataResponse)
async def get_weekly_trends_chart(
    weeks: int = Query(12, ge=1, le=52),
    current_user: User = Depends(get_current_user),
    service: ChartService = Depends(get_chart_service),
) -> ChartDataResponse:
    return await service.get_weekly_trends(current_user.id, weeks)


@router.get("/charts/monthly-trends", response_model=ChartDataResponse)
async def get_monthly_trends_chart(
    months: int = Query(12, ge=1, le=60),
    current_user: User = Depends(get_current_user),
    service: ChartService = Depends(get_chart_service),
) -> ChartDataResponse:
    return await service.get_monthly_trends(current_user.id, months)


@router.get("/charts/company-distribution", response_model=ChartDataResponse)
async def get_company_distribution_chart(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    service: ChartService = Depends(get_chart_service),
) -> ChartDataResponse:
    return await service.get_company_distribution(current_user.id, limit)


@router.get("/charts/funnel", response_model=ChartDataResponse)
async def get_funnel_chart(
    current_user: User = Depends(get_current_user),
    service: ChartService = Depends(get_chart_service),
) -> ChartDataResponse:
    return await service.get_funnel(current_user.id)


@router.get("/daily-statistics", response_model=DailyStatistics)
async def get_daily_statistics(
    date: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    service: ChartService = Depends(get_chart_service),
) -> DailyStatistics:
    return await service.get_daily_statistics(current_user.id, date)


@router.get("/reports")
async def generate_report(
    type: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    format: str = Query("csv", pattern="^(csv|xlsx|pdf)$"),
    date: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
):
    try:
        content, filename, media_type = await service.generate_report(
            current_user.id, type, format, date,
        )
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
