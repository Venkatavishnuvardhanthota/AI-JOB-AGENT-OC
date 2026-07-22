from __future__ import annotations

import re

import structlog

from app.jobs.exceptions import NormalizationError
from app.jobs.schemas import (
    CompanyInfo,
    EmploymentType,
    ExperienceLevel,
    JobPosting,
    LocationInfo,
    RemoteType,
    SalaryInfo,
)

logger = structlog.get_logger(__name__)


class JobNormalizer:
    def normalize(self, data: dict, provider: str) -> JobPosting:
        try:
            company_info = self._extract_company(data)
            job = JobPosting(
                provider_job_id=data.get("provider_job_id") or data.get("id"),
                title=self._clean_title(data.get("title", "")),
                company=company_info,
                location=self._extract_location(data),
                description=self._clean_html(data.get("description")),
                description_html=data.get("description_html") or data.get("description"),
                url=data.get("url") or data.get("apply_url"),
                apply_url=data.get("apply_url") or data.get("url"),
                employment_type=self._normalize_employment_type(data.get("employment_type")),
                experience_level=self._normalize_experience_level(data.get("experience_level")),
                salary=self._extract_salary(data),
                skills=data.get("skills") or data.get("keywords") or [],
                posted_date=data.get("posted_date") or data.get("date_posted"),
                expiration_date=data.get("expiration_date"),
                provider=provider,
                source_updated_at=data.get("updated_at"),
            )
            return job
        except Exception as exc:
            logger.error("Failed to normalize job data", provider=provider, error=str(exc))
            raise NormalizationError(f"Failed to normalize job data from '{provider}': {exc}") from exc

    def _clean_title(self, title: str) -> str:
        return title.strip() if title else "Untitled Position"

    def _clean_html(self, text: str | None) -> str | None:
        if not text:
            return None
        cleaned = re.sub(r"<[^>]+>", " ", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _extract_company(self, data: dict) -> CompanyInfo:
        raw = data.get("company") or data.get("employer") or {}
        if isinstance(raw, str):
            return CompanyInfo(name=raw)
        return CompanyInfo(
            name=raw.get("name", raw.get("company_name", raw.get("employer_name", "Unknown Company"))),
            website=raw.get("website") or raw.get("url"),
            logo_url=raw.get("logo") or raw.get("logo_url"),
            description=raw.get("description"),
            industry=raw.get("industry"),
            size=raw.get("size") or raw.get("company_size"),
        )

    def _extract_location(self, data: dict) -> LocationInfo:
        raw = data.get("location") or data.get("locations") or {}
        if isinstance(raw, str):
            return LocationInfo(display_name=raw)

        remote_raw = raw.get("remote_type") or data.get("remote_type") or data.get("remote")
        remote = RemoteType.UNKNOWN
        if remote_raw:
            remote_str = str(remote_raw).lower()
            if remote_str in ("remote", "yes", "true", "fully_remote"):
                remote = RemoteType.REMOTE
            elif remote_str in ("hybrid", "partial"):
                remote = RemoteType.HYBRID
            elif remote_str in ("on-site", "onsite", "office", "no"):
                remote = RemoteType.ON_SITE

        return LocationInfo(
            city=raw.get("city"),
            state=raw.get("state") or raw.get("region"),
            country=raw.get("country"),
            remote_type=remote,
            display_name=raw.get("display_name") or raw.get("name"),
            latitude=raw.get("latitude") or raw.get("lat"),
            longitude=raw.get("longitude") or raw.get("lng"),
        )

    def _extract_salary(self, data: dict) -> SalaryInfo | None:
        raw = data.get("salary") or data.get("compensation") or {}
        if not raw:
            return None
        if isinstance(raw, int | float):
            return SalaryInfo(min_amount=float(raw))

        min_val = raw.get("min") or raw.get("min_amount") or raw.get("minimum")
        max_val = raw.get("max") or raw.get("max_amount") or raw.get("maximum")
        if min_val is None and max_val is None:
            return None

        return SalaryInfo(
            min_amount=float(min_val) if min_val is not None else None,
            max_amount=float(max_val) if max_val is not None else None,
            currency=raw.get("currency", "USD"),
            period=raw.get("period", "yearly"),
            interval=raw.get("interval"),
        )

    def _normalize_employment_type(self, value: str | None) -> EmploymentType:
        if not value:
            return EmploymentType.OTHER
        v = str(value).lower().replace("-", "_").replace(" ", "_")
        mapping: dict[str, EmploymentType] = {
            "full_time": EmploymentType.FULL_TIME,
            "fulltime": EmploymentType.FULL_TIME,
            "full time": EmploymentType.FULL_TIME,
            "part_time": EmploymentType.PART_TIME,
            "parttime": EmploymentType.PART_TIME,
            "part time": EmploymentType.PART_TIME,
            "contract": EmploymentType.CONTRACT,
            "contractor": EmploymentType.CONTRACT,
            "temporary": EmploymentType.TEMPORARY,
            "temp": EmploymentType.TEMPORARY,
            "internship": EmploymentType.INTERNSHIP,
            "intern": EmploymentType.INTERNSHIP,
            "freelance": EmploymentType.FREELANCE,
            "freelancer": EmploymentType.FREELANCE,
        }
        return mapping.get(v, EmploymentType.OTHER)

    def _normalize_experience_level(self, value: str | None) -> ExperienceLevel:
        if not value:
            return ExperienceLevel.UNKNOWN
        v = str(value).lower().replace("-", "_").replace(" ", "_")
        mapping: dict[str, ExperienceLevel] = {
            "entry": ExperienceLevel.ENTRY,
            "entry_level": ExperienceLevel.ENTRY,
            "entrylevel": ExperienceLevel.ENTRY,
            "junior": ExperienceLevel.JUNIOR,
            "mid": ExperienceLevel.MID,
            "mid_level": ExperienceLevel.MID,
            "midlevel": ExperienceLevel.MID,
            "senior": ExperienceLevel.SENIOR,
            "sr": ExperienceLevel.SENIOR,
            "lead": ExperienceLevel.LEAD,
            "principal": ExperienceLevel.LEAD,
            "staff": ExperienceLevel.LEAD,
            "executive": ExperienceLevel.EXECUTIVE,
            "director": ExperienceLevel.EXECUTIVE,
            "vp": ExperienceLevel.EXECUTIVE,
            "c_level": ExperienceLevel.EXECUTIVE,
            "clevel": ExperienceLevel.EXECUTIVE,
        }
        return mapping.get(v, ExperienceLevel.UNKNOWN)
