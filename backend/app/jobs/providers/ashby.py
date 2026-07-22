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


class AshbyJobProvider(BaseJobProvider):
    name = "ashby"
    display_name = "Ashby"
    description = "Ashby ATS job board listings"
    version = "1.0.0"
    supports_pagination = True
    supports_filters = True

    base_url = "https://api.ashbyhq.com/posting-api"
    api_key_scheme = ""
    page_size = 20

    _board: str = "example"

    def __init__(self, config: JobDiscoveryConfig) -> None:
        self.base_url = config.ashby.base_url
        self.page_size = config.ashby.page_size
        super().__init__(config)

    def _resolve_api_key(self) -> str | None:
        return None

    async def search_jobs(self, request: JobSearchRequest) -> JobSearchResponse:
        path = f"/job-board/{self._board}"
        params = self._build_search_params(request)

        data = await self._client.get(path, params=params)
        return self._parse_response(data, request)

    def _build_search_params(self, request: JobSearchRequest) -> dict:
        params: dict = {}

        query = request.query or (" ".join(request.keywords) if request.keywords else None)
        if query:
            params["search"] = query

        if request.location:
            params["location"] = request.location

        return params

    def _parse_response(self, data: dict, request: JobSearchRequest) -> JobSearchResponse:
        raw_results = []
        if isinstance(data, dict):
            raw_results = data.get("jobs", data.get("list", []))

        total = len(raw_results)
        start = request.offset
        end = start + self._page_limit(request)
        paged = raw_results[start:end]

        postings: list[JobPosting] = []
        for raw in paged:
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
        company_raw = raw.get("company", raw.get("organization", {})) or {}
        company = CompanyInfo(
            name=company_raw.get("name", "Unknown Company"),
            description=company_raw.get("description"),
        )

        location = self._parse_location(raw)
        salary = self._parse_salary(raw)
        title = raw.get("title", raw.get("name", "Untitled Position"))
        description = raw.get("descriptionHtml", raw.get("description", ""))
        url = raw.get("url", raw.get("jobUrl", ""))

        return JobPosting(
            provider_job_id=raw.get("id", raw.get("jobId", "")),
            title=title,
            company=company,
            location=location,
            description=description,
            url=url,
            apply_url=url,
            employment_type=self._normalize_employment(raw),
            experience_level=self._normalize_experience(title),
            salary=salary,
            skills=raw.get("skills", []) or [],
            posted_date=raw.get("publishedDate", raw.get("createdAt")),
            provider=self.name,
        )

    def _parse_location(self, raw: dict) -> LocationInfo:
        loc_raw = raw.get("location", {})
        if isinstance(loc_raw, dict):
            city = loc_raw.get("city", "")
            state = loc_raw.get("state", loc_raw.get("region", ""))
            country = loc_raw.get("country", "")
            display = ", ".join(p for p in [city, state, country] if p)
        else:
            display = str(loc_raw) if loc_raw else ""

        remote = RemoteType.REMOTE if raw.get("isRemote") or "remote" in display.lower() else RemoteType.ON_SITE
        return LocationInfo(display_name=display, remote_type=remote)

    def _parse_salary(self, raw: dict) -> SalaryInfo | None:
        sal_raw = raw.get("salary", raw.get("compensation", {}))
        if isinstance(sal_raw, dict):
            salary_min = sal_raw.get("min") or sal_raw.get("min_amount") or sal_raw.get("minimum")
            salary_max = sal_raw.get("max") or sal_raw.get("max_amount") or sal_raw.get("maximum")
            currency = sal_raw.get("currency", "USD")
            if salary_min or salary_max:
                return SalaryInfo(
                    min_amount=float(salary_min) if salary_min else None,
                    max_amount=float(salary_max) if salary_max else None,
                    currency=currency,
                    period="yearly",
                )

        salary_range = raw.get("salaryRange", raw.get("salary_range", ""))
        if isinstance(salary_range, str) and salary_range:
            try:
                cleaned = salary_range.replace("$", "").replace(",", "").replace("k", "000").strip()
                parts = cleaned.split("-")
                min_sal = float(parts[0].strip()) if parts else None
                max_sal = float(parts[1].strip()) if len(parts) > 1 else None
                return SalaryInfo(min_amount=min_sal, max_amount=max_sal, currency="USD", period="yearly")
            except (ValueError, IndexError):
                pass

        return None

    def _normalize_employment(self, raw: dict) -> EmploymentType:
        emp_type = raw.get("employmentType", raw.get("type", raw.get("employment_type", "")))
        if isinstance(emp_type, dict):
            emp_type = emp_type.get("name", "")
        emp_str = str(emp_type).lower() if emp_type else ""
        if "full" in emp_str or "permanent" in emp_str:
            return EmploymentType.FULL_TIME
        if "part" in emp_str:
            return EmploymentType.PART_TIME
        if "contract" in emp_str:
            return EmploymentType.CONTRACT
        if "intern" in emp_str:
            return EmploymentType.INTERNSHIP
        if "temp" in emp_str:
            return EmploymentType.TEMPORARY
        if "freelance" in emp_str:
            return EmploymentType.FREELANCE
        return EmploymentType.OTHER

    def _normalize_experience(self, title: str) -> ExperienceLevel:
        title_lower = title.lower()
        if any(kw in title_lower for kw in ("senior", "sr.", "lead", "principal", "staff", "head")):
            return ExperienceLevel.SENIOR
        if any(kw in title_lower for kw in ("junior", "jr.", "graduate", "entry")):
            return ExperienceLevel.JUNIOR
        if any(kw in title_lower for kw in ("director", "vp", "chief", "executive")):
            return ExperienceLevel.EXECUTIVE
        if any(kw in title_lower for kw in ("intern", "trainee")):
            return ExperienceLevel.ENTRY
        return ExperienceLevel.MID

    async def _fetch_provider_status(self) -> object:
        data = await self._client.get(f"/job-board/{self._board}")
        return data
