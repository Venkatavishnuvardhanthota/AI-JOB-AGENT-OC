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


class AdzunaJobProvider(BaseJobProvider):
    name = "adzuna"
    display_name = "Adzuna"
    description = "Adzuna job search API"
    version = "1.0.0"
    supports_pagination = True
    supports_filters = True

    base_url = "https://api.adzuna.com/v1/api/jobs"
    api_key_header = "Authorization"
    api_key_scheme = ""
    page_size = 20

    def __init__(self, config: JobDiscoveryConfig) -> None:
        self.base_url = config.adzuna.base_url
        self.page_size = config.adzuna.page_size
        self._adzuna_rate = config.adzuna.rate_limit_rate
        self._adzuna_burst = config.adzuna.rate_limit_burst
        super().__init__(config)

    def _resolve_api_key(self) -> str | None:
        return None

    def _default_query_params(self) -> dict[str, str]:
        return {
            "app_id": self.config.adzuna.app_id,
            "app_key": self.config.adzuna.api_key,
            "content-type": "application/json",
        }

    async def search_jobs(self, request: JobSearchRequest) -> JobSearchResponse:
        country = "us"
        page = max(1, (request.offset // self.page_size) + 1)
        path = f"/{country}/search/{page}"

        params = self._build_search_params(request)

        data = await self._client.get(path, params=params)
        return self._parse_response(data, request)

    def _build_search_params(self, request: JobSearchRequest) -> dict:
        params: dict = {
            "results_per_page": self._page_limit(request),
        }

        query = request.query or (" ".join(request.keywords) if request.keywords else None)
        if query:
            params["what"] = query
        if request.location:
            params["where"] = request.location

        if request.remote_only:
            params["remote"] = 1

        if request.salary_min is not None:
            params["salary_min"] = request.salary_min
        if request.salary_max is not None:
            params["salary_max"] = request.salary_max

        if request.posted_within_days is not None:
            params["max_days_old"] = request.posted_within_days

        contract_type = self._adzuna_contract_type(request.employment_type)
        if contract_type:
            params["contract_type"] = contract_type

        return params

    def _parse_response(self, data: dict, request: JobSearchRequest) -> JobSearchResponse:
        raw_results = data.get("results", [])
        total = data.get("count", len(raw_results))

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
        loc_raw = raw.get("location", {}) or {}

        company = CompanyInfo(
            name=company_raw.get("display_name", "Unknown Company"),
        )

        display_location = loc_raw.get("display_name", "") or ""
        location = self._parse_location(display_location, raw)

        salary = self._parse_salary(raw)

        title = raw.get("title", "Untitled Position")
        description = raw.get("description", "")
        url = raw.get("redirect_url", "")

        contract_type = raw.get("contract_type")
        contract_time = raw.get("contract_time")

        return JobPosting(
            provider_job_id=str(raw.get("id", "")),
            title=title,
            company=company,
            location=location,
            description=description,
            url=url,
            apply_url=url,
            employment_type=self._normalize_employment(contract_type, contract_time),
            experience_level=self._normalize_experience(title, raw.get("category", {})),
            salary=salary,
            skills=[],
            posted_date=self._parse_date(raw.get("created")),
            provider=self.name,
        )

    def _parse_location(self, display: str, raw: dict) -> LocationInfo:
        remote = RemoteType.ON_SITE
        if raw.get("remote") or raw.get("remote_type"):
            remote = RemoteType.REMOTE
        parts = [p.strip() for p in display.split(",") if p.strip()]
        city = parts[0] if parts else None
        state = parts[1] if len(parts) >= 2 else None
        country = parts[2] if len(parts) >= 3 else None
        return LocationInfo(
            city=city,
            state=state,
            country=country,
            remote_type=remote,
            display_name=display,
        )

    def _parse_salary(self, raw: dict) -> SalaryInfo | None:
        salary_min = raw.get("salary_min")
        salary_max = raw.get("salary_max")
        currency = raw.get("salary_currency", "USD")
        is_predicted = raw.get("salary_is_predicted", False)

        if salary_min is None and salary_max is None:
            return None

        return SalaryInfo(
            min_amount=float(salary_min) if salary_min is not None else None,
            max_amount=float(salary_max) if salary_max is not None else None,
            currency=currency if currency else "USD",
            period="yearly",
            interval="predicted" if is_predicted else None,
        )

    def _normalize_employment(self, contract_type: str | None, contract_time: str | None) -> EmploymentType:
        if contract_type == "permanent" or contract_time == "full_time":
            return EmploymentType.FULL_TIME
        if contract_type == "contract":
            return EmploymentType.CONTRACT
        if contract_time == "part_time":
            return EmploymentType.PART_TIME
        if contract_type == "internship":
            return EmploymentType.INTERNSHIP
        return EmploymentType.OTHER

    def _normalize_experience(self, title: str, category: dict) -> ExperienceLevel:
        title_lower = title.lower()
        if any(kw in title_lower for kw in ("senior", "sr.", "lead", "principal", "staff", "head")):
            return ExperienceLevel.SENIOR
        if any(kw in title_lower for kw in ("junior", "jr.", "graduate", "entry")):
            return ExperienceLevel.JUNIOR
        if any(kw in title_lower for kw in ("director", "vp", "chief", "executive", "c-level")):
            return ExperienceLevel.EXECUTIVE
        if any(kw in title_lower for kw in ("intern", "trainee")):
            return ExperienceLevel.ENTRY
        return ExperienceLevel.MID

    def _adzuna_contract_type(self, emp_type: EmploymentType | None) -> str | None:
        if emp_type is None:
            return None
        mapping = {
            EmploymentType.FULL_TIME: "permanent",
            EmploymentType.PART_TIME: "part_time",
            EmploymentType.CONTRACT: "contract",
            EmploymentType.INTERNSHIP: "internship",
        }
        return mapping.get(emp_type)

    @staticmethod
    def _parse_date(date_str: str | None) -> str | None:
        return date_str

    async def _fetch_provider_status(self) -> object:
        data = await self._client.get("/us/search/1", params={"results_per_page": 1, "what": "test"})
        return data
