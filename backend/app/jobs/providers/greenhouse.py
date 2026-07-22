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


class GreenhouseJobProvider(BaseJobProvider):
    name = "greenhouse"
    display_name = "Greenhouse"
    description = "Greenhouse ATS job board listings"
    version = "1.0.0"
    supports_pagination = True
    supports_filters = True

    base_url = "https://boards-api.greenhouse.io/v1/boards"
    api_key_scheme = ""
    page_size = 20

    _board_token: str = "example"

    def __init__(self, config: JobDiscoveryConfig) -> None:
        self.base_url = config.greenhouse.base_url
        self.page_size = config.greenhouse.page_size
        super().__init__(config)

    def _resolve_api_key(self) -> str | None:
        return None

    async def search_jobs(self, request: JobSearchRequest) -> JobSearchResponse:
        page = max(1, (request.offset // self.page_size) + 1)
        path = f"/{self._board_token}/jobs"
        params = self._build_search_params(request)
        params["page"] = page

        data = await self._client.get(path, params=params)
        return self._parse_response(data, request)

    def _build_search_params(self, request: JobSearchRequest) -> dict:
        params: dict = {"per_page": self._page_limit(request)}

        query = request.query or (" ".join(request.keywords) if request.keywords else None)
        if query:
            params["query"] = query

        if request.location:
            params["location"] = request.location

        return params

    def _parse_response(self, data: dict, request: JobSearchRequest) -> JobSearchResponse:
        raw_results = data.get("jobs", [])
        total = data.get("meta", {}).get("total", len(raw_results))

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
        company_raw = raw.get("company", raw.get("metadata", {})) or {}
        offices = raw.get("offices", [])

        company_name = "Unknown Company"
        if isinstance(company_raw, dict):
            company_name = company_raw.get("name", "Unknown Company")
        elif raw.get("board_token"):
            company_name = raw["board_token"].replace("-", " ").title()

        company = CompanyInfo(name=company_name)

        location = self._parse_location(raw, offices)
        salary = self._parse_salary(raw)
        title = raw.get("title", "Untitled Position")
        description = self._extract_description(raw)
        url = raw.get("absolute_url", "")

        return JobPosting(
            provider_job_id=str(raw.get("id", "")),
            title=title,
            company=company,
            location=location,
            description=description,
            url=url,
            apply_url=url,
            employment_type=self._normalize_employment(raw.get("metadata", {})),
            experience_level=self._normalize_experience(title),
            salary=salary,
            skills=[],
            posted_date=raw.get("updated_at"),
            provider=self.name,
        )

    def _parse_location(self, raw: dict, offices: list) -> LocationInfo:
        offices_str = ", ".join(o.get("name", "") for o in offices) if offices else ""
        loc = raw.get("location", "")
        display = loc.get("name", "") if isinstance(loc, dict) else str(loc)
        display = display or offices_str or ""
        remote = RemoteType.REMOTE if "remote" in display.lower() else RemoteType.ON_SITE
        return LocationInfo(display_name=display, remote_type=remote)

    def _parse_salary(self, raw: dict) -> SalaryInfo | None:
        metadata = raw.get("metadata", {})
        if isinstance(metadata, dict):
            for field in metadata.get("fields", []):
                if "salary" in field.get("name", "").lower() and field.get("value"):
                    try:
                        val = float(field["value"].replace("$", "").replace(",", "").split("-")[0].strip())
                        return SalaryInfo(min_amount=val, currency="USD", period="yearly")
                    except (ValueError, IndexError):
                        pass
        return None

    def _extract_description(self, raw: dict) -> str | None:
        content = raw.get("content") or raw.get("description") or ""
        if isinstance(content, str):
            return content
        return None

    def _normalize_employment(self, metadata: dict) -> EmploymentType:
        if not isinstance(metadata, dict):
            return EmploymentType.OTHER
        for field in metadata.get("fields", []):
            name = field.get("name", "").lower()
            value = str(field.get("value", "")).lower()
            if "employment" in name or "type" in name:
                if "full" in value or "permanent" in value:
                    return EmploymentType.FULL_TIME
                if "part" in value:
                    return EmploymentType.PART_TIME
                if "contract" in value:
                    return EmploymentType.CONTRACT
                if "intern" in value:
                    return EmploymentType.INTERNSHIP
                if "temp" in value:
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

    async def _fetch_provider_status(self) -> object:
        data = await self._client.get(f"/{self._board_token}/jobs", params={"per_page": 1})
        return data
