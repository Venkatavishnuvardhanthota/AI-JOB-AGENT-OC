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


class WorkdayJobProvider(BaseJobProvider):
    name = "workday"
    display_name = "Workday"
    description = "Workday career portal job listings"
    version = "1.0.0"
    supports_pagination = True
    supports_filters = True

    base_url = "https://wd5.myworkdayjobs.com/wday/cxs"
    api_key_scheme = ""
    page_size = 20

    _tenant: str = "default"

    def __init__(self, config: JobDiscoveryConfig) -> None:
        self.base_url = config.workday.base_url
        self.page_size = config.workday.page_size
        self._tenant = config.workday.tenant
        super().__init__(config)

    def _resolve_api_key(self) -> str | None:
        return None

    async def search_jobs(self, request: JobSearchRequest) -> JobSearchResponse:
        page = max(1, (request.offset // self.page_size) + 1)
        path = f"/{self._tenant}/jobs"
        params = self._build_search_params(request)
        params["page"] = page

        data = await self._client.get(path, params=params)
        return self._parse_response(data, request)

    def _build_search_params(self, request: JobSearchRequest) -> dict:
        params: dict = {"limit": self._page_limit(request)}

        query = request.query or (" ".join(request.keywords) if request.keywords else None)
        if query:
            params["search"] = query

        if request.location:
            params["location"] = request.location

        return params

    def _parse_response(self, data: dict, request: JobSearchRequest) -> JobSearchResponse:
        raw_results = data.get("jobPostings", data.get("jobs", data.get("results", [])))
        total = data.get("total", data.get("totalCount", len(raw_results)))

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
        company_raw = raw.get("company", raw.get("employer", {})) or {}
        company = CompanyInfo(
            name=company_raw.get("name", raw.get("companyName", raw.get("postedBy", "Unknown Company"))),
        )

        location = self._parse_location(raw)
        salary = self._parse_salary(raw)
        title = raw.get("title", raw.get("jobTitle", raw.get("displayName", "Untitled Position")))
        description = raw.get("description", raw.get("jobDescription", raw.get("descriptionText", "")))
        url = raw.get("url", raw.get("jobUrl", "")) or raw.get("applyUrl", "")

        return JobPosting(
            provider_job_id=str(raw.get("id", raw.get("jobId", raw.get("bulletId", "")))),
            title=title,
            company=company,
            location=location,
            description=description,
            url=url,
            apply_url=url,
            employment_type=self._normalize_employment(raw),
            experience_level=self._normalize_experience(title),
            salary=salary,
            skills=raw.get("skills", raw.get("skillTags", [])) or [],
            posted_date=raw.get("postedDate", raw.get("createdDate", raw.get("publishedDate"))),
            provider=self.name,
        )

    def _parse_location(self, raw: dict) -> LocationInfo:
        loc_raw = raw.get("location", raw.get("locations", raw.get("jobLocation", {})))
        if isinstance(loc_raw, dict):
            city = loc_raw.get("city", loc_raw.get("name", ""))
            state = loc_raw.get("state", loc_raw.get("region", ""))
            country = loc_raw.get("country", loc_raw.get("countryCode", ""))
            display = ", ".join(p for p in [city, state, country] if p)
        elif isinstance(loc_raw, list):
            display = ", ".join(str(item) for item in loc_raw)
        else:
            display = str(loc_raw) if loc_raw else ""

        is_remote = raw.get("remote") or raw.get("isRemote") or raw.get("workFromHome")
        remote = RemoteType.REMOTE if is_remote else RemoteType.ON_SITE
        return LocationInfo(display_name=display, remote_type=remote)

    def _parse_salary(self, raw: dict) -> SalaryInfo | None:
        salary_min = raw.get("salaryMin", raw.get("minSalary", raw.get("salaryMinimum")))
        salary_max = raw.get("salaryMax", raw.get("maxSalary", raw.get("salaryMaximum")))
        currency = raw.get("salaryCurrency", raw.get("currency", "USD"))

        if salary_min is not None or salary_max is not None:
            return SalaryInfo(
                min_amount=float(salary_min) if salary_min is not None else None,
                max_amount=float(salary_max) if salary_max is not None else None,
                currency=currency,
                period="yearly",
            )

        salary_range = raw.get("salaryRange", raw.get("salary", ""))
        if isinstance(salary_range, str) and salary_range:
            try:
                cleaned = salary_range.replace("$", "").replace(",", "").strip()
                parts = cleaned.split("-")
                min_sal = float(parts[0].strip()) if parts else None
                max_sal = float(parts[1].strip()) if len(parts) > 1 else None
                return SalaryInfo(min_amount=min_sal, max_amount=max_sal, currency=currency, period="yearly")
            except (ValueError, IndexError):
                pass

        return None

    def _normalize_employment(self, raw: dict) -> EmploymentType:
        emp_type = raw.get("employmentType", raw.get("type", raw.get("employment_type", raw.get("workShift", ""))))
        if isinstance(emp_type, dict):
            emp_type = emp_type.get("name", "")
        emp_str = str(emp_type).lower() if emp_type else ""
        if "full" in emp_str or "permanent" in emp_str or "regular" in emp_str:
            return EmploymentType.FULL_TIME
        if "part" in emp_str:
            return EmploymentType.PART_TIME
        if "contract" in emp_str or "temporary" in emp_str:
            return EmploymentType.CONTRACT
        if "intern" in emp_str:
            return EmploymentType.INTERNSHIP
        if "temp" in emp_str:
            return EmploymentType.TEMPORARY
        return EmploymentType.OTHER

    def _normalize_experience(self, title: str) -> ExperienceLevel:
        title_lower = title.lower()
        if any(kw in title_lower for kw in ("senior", "sr.", "lead", "principal", "staff", "head", "expert")):
            return ExperienceLevel.SENIOR
        if any(kw in title_lower for kw in ("junior", "jr.", "graduate", "entry", "associate")):
            return ExperienceLevel.JUNIOR
        if any(kw in title_lower for kw in ("director", "vp", "vice president", "chief", "executive")):
            return ExperienceLevel.EXECUTIVE
        if any(kw in title_lower for kw in ("intern", "trainee")):
            return ExperienceLevel.ENTRY
        return ExperienceLevel.MID

    async def _fetch_provider_status(self) -> object:
        data = await self._client.get(f"/{self._tenant}/jobs", params={"limit": 1})
        return data
