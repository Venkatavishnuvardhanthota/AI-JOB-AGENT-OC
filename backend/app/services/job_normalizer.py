import hashlib
import logging
from datetime import datetime

from app.schemas.job import JobCreate
from app.services.providers.base import RawJobData

logger = logging.getLogger(__name__)


class JobNormalizer:
    """Normalizes RawJobData from various providers into unified JobCreate schemas."""

    SOURCE_PRIORITY = {
        "greenhouse": 10,
        "lever": 10,
        "ashby": 10,
        "ycombinator": 9,
        "remoteok": 8,
        "linkedin": 7,
        "indeed": 7,
        "naukri": 6,
        "wellfound": 6,
        "foundit": 5,
        "weworkremotely": 5,
        "unstop": 4,
        "google_jobs": 4,
        "internshala": 3,
        "workday": 3,
        "freshersworld": 2,
        "career_pages": 2,
    }

    def normalize(self, raw: RawJobData) -> JobCreate:
        """Convert a RawJobData to a JobCreate with content hash."""
        content_hash = self._compute_hash(raw)
        now = datetime.utcnow()

        return JobCreate(
            title=self._clean_text(raw.title, 255),
            company_name=self._clean_text(raw.company_name, 255),
            company_url=raw.company_url,
            company_logo_url=raw.company_logo_url,
            location=self._clean_text(raw.location, 255),
            description=raw.description,
            url=raw.url,
            source=raw.raw.get("source", "unknown") if raw.raw else "unknown",
            source_job_id=raw.source_job_id,
            salary_min=raw.salary_min,
            salary_max=raw.salary_max,
            salary_currency=raw.salary_currency or "USD",
            salary_period=raw.salary_period or "yearly",
            posted_at=raw.posted_at or now,
            job_type=raw.job_type,
            remote=raw.remote,
            apply_url=raw.apply_url or raw.url,
            skills=raw.skills or [],
            requirements=raw.requirements or [],
            benefits=raw.benefits or [],
            categories=raw.categories or [],
            content_hash=content_hash,
            raw_data=raw.raw,
        )

    def normalize_batch(self, raw_list: list[RawJobData]) -> list[JobCreate]:
        """Normalize a batch of RawJobData objects."""
        return [self.normalize(r) for r in raw_list]

    def _compute_hash(self, raw: RawJobData) -> str:
        """Compute a deterministic hash for deduplication."""
        raw_source = (raw.raw or {}).get("source", "unknown")

        if raw.source_job_id:
            hash_input = f"{raw_source}:{raw.source_job_id}"
        else:
            title = (raw.title or "").strip().lower()
            company = (raw.company_name or "").strip().lower()
            location = (raw.location or "").strip().lower()
            hash_input = f"{raw_source}:{title}:{company}:{location}"

        return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    @staticmethod
    def _clean_text(text: str | None, max_length: int = 255) -> str | None:
        if not text:
            return None
        cleaned = " ".join(text.split())
        return cleaned[:max_length] if cleaned else None
