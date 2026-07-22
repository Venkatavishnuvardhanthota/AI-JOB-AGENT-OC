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


class UnstopJobProvider(BaseJobProvider):
    name = "unstop"
    display_name = "Unstop"
    description = "Unstop (formerly Dare2Compete) opportunities and job listings"
    version = "1.0.0"
    supports_pagination = True
    supports_filters = True

    base_url = "https://unstop.com"
    api_key_scheme = ""
    page_size = 20

    def __init__(self, config: JobDiscoveryConfig) -> None:
        self.base_url = config.unstop.base_url
        self.page_size = config.unstop.page_size
        super().__init__(config)

    def _resolve_api_key(self) -> str | None:
        return None

    async def search_jobs(self, request: JobSearchRequest) -> JobSearchResponse:
        page = max(1, (request.offset // self.page_size) + 1)
        params = self._build_search_params(request)
        params["page"] = page

        data = await self._client.get("/api/opportunities", params=params)
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
        raw_results = data.get("data", data.get("opportunities", data.get("results", [])))
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
        company_raw = raw.get("company", raw.get("organization", raw.get("organiser", {}))) or {}
        company = CompanyInfo(
            name=company_raw.get("name", raw.get("companyName", raw.get("orgName", "Unknown Company"))),
            description=company_raw.get("description"),
            industry=company_raw.get("industry"),
            website=company_raw.get("website", company_raw.get("url")),
        )

        location = self._parse_location(raw)
        salary = self._parse_salary(raw)
        title = raw.get("title", raw.get("name", raw.get("opportunityName", "Untitled Position")))
        description = raw.get("description", raw.get("about", raw.get("details", "")))
        url = raw.get("url", raw.get("registrationUrl", raw.get("link", "")))

        opp_type = raw.get("type", raw.get("opportunityType", "")).lower()
        is_internship = "intern" in opp_type or "intern" in title.lower()

        return JobPosting(
            provider_job_id=str(raw.get("id", raw.get("opportunityId", raw.get("uid", "")))),
            title=title,
            company=company,
            location=location,
            description=description,
            url=url,
            apply_url=url,
            employment_type=EmploymentType.INTERNSHIP if is_internship else self._normalize_employment(raw),
            experience_level=ExperienceLevel.ENTRY if is_internship else self._normalize_experience(title),
            salary=salary,
            skills=raw.get("skills", raw.get("tags", [])) or [],
            posted_date=raw.get("postedDate", raw.get("createdAt", raw.get("created_at"))),
            provider=self.name,
        )

    def _parse_location(self, raw: dict) -> LocationInfo:
        loc_raw = raw.get("location", raw.get("locations", raw.get("venue", {})))
        if isinstance(loc_raw, dict):
            city = loc_raw.get("city", loc_raw.get("name", ""))
            state = loc_raw.get("state", "")
            country = loc_raw.get("country", "India")
            display = ", ".join(p for p in [city, state, country] if p)
        elif isinstance(loc_raw, list):
            display = ", ".join(str(loc_item) for loc_item in loc_raw)
        else:
            display = str(loc_raw) if loc_raw else ""

        remote = RemoteType.REMOTE if raw.get("remote") or raw.get("isRemote") else RemoteType.ON_SITE
        return LocationInfo(display_name=display, remote_type=remote)

    def _parse_salary(self, raw: dict) -> SalaryInfo | None:
        salary_min = raw.get("salaryMin", raw.get("minSalary", raw.get("prizeMin", raw.get("min_amount"))))
        salary_max = raw.get("salaryMax", raw.get("maxSalary", raw.get("prizeMax", raw.get("max_amount"))))
        currency = raw.get("salaryCurrency", raw.get("currency", "INR"))

        if salary_min is not None or salary_max is not None:
            return SalaryInfo(
                min_amount=float(salary_min) if salary_min is not None else None,
                max_amount=float(salary_max) if salary_max is not None else None,
                currency=currency,
                period="yearly",
            )

        salary_str = raw.get("salary", raw.get("prize", raw.get("compensation", "")))
        if isinstance(salary_str, str) and salary_str:
            try:
                cleaned = salary_str.replace("\u20b9", "").replace(",", "") \
                    .replace("L", "00000").replace("l", "00000").strip()
                parts = cleaned.split("-")
                min_sal = float(parts[0].strip()) if parts else None
                max_sal = float(parts[1].strip()) if len(parts) > 1 else None
                return SalaryInfo(min_amount=min_sal, max_amount=max_sal, currency="INR", period="yearly")
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
        if any(kw in title_lower for kw in ("intern", "trainee", "fresher")):
            return ExperienceLevel.ENTRY
        return ExperienceLevel.MID

    async def _fetch_provider_status(self) -> object:
        data = await self._client.get("/api/opportunities", params={"limit": 1})
        return data
