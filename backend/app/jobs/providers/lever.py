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


class LeverJobProvider(BaseJobProvider):
    name = "lever"
    display_name = "Lever"
    description = "Lever ATS job board listings"
    version = "1.0.0"
    supports_pagination = True
    supports_filters = True

    base_url = "https://api.lever.co/v0"
    api_key_scheme = ""
    page_size = 20

    _board: str = "example"

    def __init__(self, config: JobDiscoveryConfig) -> None:
        self.base_url = config.lever.base_url
        self.page_size = config.lever.page_size
        super().__init__(config)

    def _resolve_api_key(self) -> str | None:
        return None

    async def search_jobs(self, request: JobSearchRequest) -> JobSearchResponse:
        offset = request.offset
        path = f"/postings/{self._board}"
        params = self._build_search_params(request)
        params["offset"] = offset

        data = await self._client.get(path, params=params)
        return self._parse_response(data, request)

    def _build_search_params(self, request: JobSearchRequest) -> dict:
        params: dict = {
            "limit": self._page_limit(request),
            "mode": "json",
            "group": "team",
        }

        query = request.query or (" ".join(request.keywords) if request.keywords else None)
        if query:
            params["query"] = query

        return params

    def _parse_response(self, data: dict, request: JobSearchRequest) -> JobSearchResponse:
        raw_results = []
        if isinstance(data, dict):
            raw_results = data.get("data", []) if "data" in data else data.get("postings", [])

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
            name=company_raw.get("name", raw.get("team", "Unknown Company")),
        )

        location = self._parse_location(raw)
        salary = self._parse_salary(raw)
        title = raw.get("text", raw.get("title", "Untitled Position"))
        url = raw.get("applyUrl", raw.get("hostedUrl", ""))
        description = raw.get("descriptionPlain", raw.get("description", ""))

        return JobPosting(
            provider_job_id=raw.get("id", ""),
            title=title,
            company=company,
            location=location,
            description=description,
            url=url,
            apply_url=url,
            employment_type=self._normalize_employment(raw.get("categories", {})),
            experience_level=self._normalize_experience(title),
            salary=salary,
            skills=self._extract_lists(raw),
            posted_date=raw.get("createdAt"),
            provider=self.name,
        )

    def _parse_location(self, raw: dict) -> LocationInfo:
        loc_raw = raw.get("location", "")
        if isinstance(loc_raw, dict):
            display = loc_raw.get("name", loc_raw.get("location", ""))
        else:
            display = str(loc_raw) if loc_raw else ""

        remote = RemoteType.REMOTE if "remote" in display.lower() else RemoteType.ON_SITE
        return LocationInfo(display_name=display, remote_type=remote)

    def _parse_salary(self, raw: dict) -> SalaryInfo | None:
        cats = raw.get("categories", {})
        if isinstance(cats, dict):
            salary_str = cats.get("salary", "") or cats.get("compensation", "")
            if salary_str:
                try:
                    cleaned = salary_str.replace("$", "").replace(",", "").replace("/yr", "").strip()
                    parts = cleaned.split("-")
                    min_sal = float(parts[0].strip()) if parts else None
                    max_sal = float(parts[1].strip()) if len(parts) > 1 else None
                    return SalaryInfo(min_amount=min_sal, max_amount=max_sal, currency="USD", period="yearly")
                except (ValueError, IndexError):
                    pass

        salary_min = raw.get("salary_min") or raw.get("salaryLow")
        salary_max = raw.get("salary_max") or raw.get("salaryHigh")
        if salary_min or salary_max:
            return SalaryInfo(
                min_amount=float(salary_min) if salary_min else None,
                max_amount=float(salary_max) if salary_max else None,
                currency="USD",
                period="yearly",
            )
        return None

    def _normalize_employment(self, categories: dict) -> EmploymentType:
        if not isinstance(categories, dict):
            return EmploymentType.OTHER
        commitment = (categories.get("commitment", "") or categories.get("type", "") or "").lower()
        if "full" in commitment or "permanent" in commitment:
            return EmploymentType.FULL_TIME
        if "part" in commitment:
            return EmploymentType.PART_TIME
        if "contract" in commitment:
            return EmploymentType.CONTRACT
        if "intern" in commitment:
            return EmploymentType.INTERNSHIP
        if "temp" in commitment:
            return EmploymentType.TEMPORARY
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

    def _extract_lists(self, raw: dict) -> list[str]:
        skills = []
        for lst in raw.get("lists", []):
            if isinstance(lst, dict):
                for item in lst.get("items", []):
                    if isinstance(item, dict) and item.get("content"):
                        skills.append(item["content"])
                    elif isinstance(item, str):
                        skills.append(item)
        return skills

    async def _fetch_provider_status(self) -> object:
        data = await self._client.get(f"/postings/{self._board}", params={"limit": 1, "mode": "json"})
        return data
