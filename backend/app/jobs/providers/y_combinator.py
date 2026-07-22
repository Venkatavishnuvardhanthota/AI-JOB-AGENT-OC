from __future__ import annotations

import structlog

from app.jobs.base_provider import BaseJobProvider
from app.jobs.config import JobDiscoveryConfig
from app.jobs.schemas import (
    CompanyInfo,
    EmploymentType,
    ExperienceLevel,
    JobPosting,
    JobSearchRequest,
    JobSearchResponse,
    LocationInfo,
    RemoteType,
    SalaryInfo,
    SearchMetadata,
)

logger = structlog.get_logger(__name__)


class YCombinatorJobProvider(BaseJobProvider):
    name = "y_combinator"
    display_name = "Y Combinator"
    description = "Y Combinator Work at a Startup job listings"
    version = "1.0.0"
    supports_pagination = True
    supports_filters = True

    base_url = "https://www.workatastartup.com"
    api_key_scheme = ""
    page_size = 20

    def __init__(self, config: JobDiscoveryConfig) -> None:
        self.base_url = config.y_combinator.base_url
        self.page_size = config.y_combinator.page_size
        super().__init__(config)

    def _resolve_api_key(self) -> str | None:
        return None

    async def search_jobs(self, request: JobSearchRequest) -> JobSearchResponse:
        page = max(1, (request.offset // self.page_size) + 1)
        params = self._build_search_params(request)
        params["page"] = page

        data = await self._client.get("/jobs", params=params)
        return self._parse_response(data, request)

    def _build_search_params(self, request: JobSearchRequest) -> dict:
        params: dict = {"limit": self._page_limit(request)}

        query = request.query or (" ".join(request.keywords) if request.keywords else None)
        if query:
            params["query"] = query

        if request.location:
            params["location"] = request.location

        if request.remote_only:
            params["remote"] = "true"

        return params

    def _parse_response(self, data: dict, request: JobSearchRequest) -> JobSearchResponse:
        raw_results = data.get("jobs", [])
        total = data.get("total", len(raw_results))

        postings: list[JobPosting] = []
        for raw in raw_results:
            posting = self._raw_to_posting(raw)
            postings.append(posting)

        metadata = SearchMetadata(
            total_results=total,
            returned_results=len(postings),
            providers_queried=[self.name],
            providers_succeeded=[self.name],
        )
        return JobSearchResponse(results=postings, metadata=metadata)

    def _raw_to_posting(self, raw: dict) -> JobPosting:
        company_raw = raw.get("company", {}) or {}
        company = CompanyInfo(
            name=company_raw.get("name", "Unknown Company"),
            description=company_raw.get("description") or company_raw.get("one_liner"),
            size=str(company_raw.get("team_size", "")) if company_raw.get("team_size") else None,
            website=company_raw.get("url"),
        )

        location = self._parse_location(raw)

        salary = self._parse_salary(raw)

        title = raw.get("title", "Untitled Position")
        description = raw.get("description", "")
        url = raw.get("url", "")
        apply_url = raw.get("url", "") or raw.get("apply_url", "")

        return JobPosting(
            provider_job_id=str(raw.get("id", "")),
            title=title,
            company=company,
            location=location,
            description=description,
            url=url,
            apply_url=apply_url,
            employment_type=self._normalize_employment(raw),
            experience_level=self._normalize_experience(title),
            salary=salary,
            skills=raw.get("skills", []) or [],
            posted_date=raw.get("created_at"),
            provider=self.name,
        )

    def _parse_location(self, raw: dict) -> LocationInfo:
        display = (raw.get("location") or raw.get("locations") or "")
        remote = RemoteType.REMOTE if raw.get("remote") else RemoteType.ON_SITE

        if isinstance(display, list):
            return LocationInfo(display_name=", ".join(display), remote_type=remote)

        return LocationInfo(display_name=str(display) if display else "", remote_type=remote)

    def _parse_salary(self, raw: dict) -> SalaryInfo | None:
        salary_min = raw.get("salary_min") or raw.get("salary_low")
        salary_max = raw.get("salary_max") or raw.get("salary_high")
        equity = raw.get("equity")

        if salary_min is None and salary_max is None:
            return None

        return SalaryInfo(
            min_amount=float(salary_min) if salary_min is not None else None,
            max_amount=float(salary_max) if salary_max is not None else None,
            currency=raw.get("salary_currency", "USD"),
            period="yearly",
            interval=f"equity: {equity}" if equity else None,
        )

    def _normalize_employment(self, raw: dict) -> EmploymentType:
        job_type = raw.get("job_type", "")
        if job_type == "internship":
            return EmploymentType.INTERNSHIP
        if job_type == "contract":
            return EmploymentType.CONTRACT
        if job_type == "part-time":
            return EmploymentType.PART_TIME
        return EmploymentType.FULL_TIME

    def _normalize_experience(self, title: str) -> ExperienceLevel:
        title_lower = title.lower()
        if any(kw in title_lower for kw in ("senior", "sr.", "lead", "principal", "staff", "head")):
            return ExperienceLevel.SENIOR
        if any(kw in title_lower for kw in ("junior", "jr.", "graduate", "entry")):
            return ExperienceLevel.JUNIOR
        if any(kw in title_lower for kw in ("intern", "trainee")):
            return ExperienceLevel.ENTRY
        return ExperienceLevel.MID

    async def _fetch_provider_status(self) -> object:
        data = await self._client.get("/jobs", params={"limit": 1})
        return data
