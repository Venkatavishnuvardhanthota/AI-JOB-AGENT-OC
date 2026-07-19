from datetime import datetime
from typing import Any

from pydantic import BaseModel


class StatusCount(BaseModel):
    status: str
    count: int


class TopCompany(BaseModel):
    company_name: str
    count: int


class DashboardSummary(BaseModel):
    total_applications: int
    active_applications: int
    applications_this_week: int
    applications_this_month: int
    interviews_scheduled: int
    offers_received: int
    interview_rate: float
    success_rate: float
    status_breakdown: list[StatusCount]


class TrendDataPoint(BaseModel):
    date: str
    count: int


class DailyStatistics(BaseModel):
    date: str
    applications_created: int
    status_breakdown: list[StatusCount]


class StatisticsResponse(BaseModel):
    period: str
    from_date: datetime | None = None
    to_date: datetime | None = None
    total_applications: int
    status_breakdown: list[StatusCount]
    daily_trend: list[TrendDataPoint]
    weekly_trend: list[TrendDataPoint]
    monthly_trend: list[TrendDataPoint]
    previous_period_total: int
    growth_percentage: float | None
    top_companies: list[TopCompany]
    interview_rate: float
    success_rate: float


class ChartDataset(BaseModel):
    label: str
    data: list[int | float]
    backgroundColor: list[str] | None = None  # noqa: N815
    borderColor: str | None = None  # noqa: N815


class ChartDataResponse(BaseModel):
    labels: list[str]
    datasets: list[ChartDataset]


class ReportRequest(BaseModel):
    type: str = "daily"
    format: str = "csv"
    date: str | None = None


class ReportInfo(BaseModel):
    type: str
    format: str
    period: str
    generated_at: datetime
    total_applications: int
    status_breakdown: list[StatusCount]
    top_companies: list[TopCompany]
    interview_rate: float
    success_rate: float
    daily_breakdown: list[dict[str, Any]] | None = None
    weekly_breakdown: list[dict[str, Any]] | None = None
