from __future__ import annotations

import structlog

from app.jobs.config import JobDiscoveryConfig
from app.jobs.exceptions import DuplicateDetectionError
from app.jobs.schemas import JobPosting

logger = structlog.get_logger(__name__)


class DeduplicationEngine:
    def __init__(self, config: JobDiscoveryConfig) -> None:
        self._config = config

    def deduplicate(self, postings: list[JobPosting]) -> list[JobPosting]:
        if not postings:
            return []

        try:
            seen: set[str] = set()
            result: list[JobPosting] = []
            for posting in postings:
                key = self._make_key(posting)
                if key and key not in seen:
                    seen.add(key)
                    result.append(posting)
                elif not key:
                    result.append(posting)
            return result
        except Exception as exc:
            raise DuplicateDetectionError(f"Duplicate detection failed: {exc}") from exc

    def _make_key(self, posting: JobPosting) -> str | None:
        if self._config.dedup_by_provider_id and posting.provider_job_id:
            return f"provider_id:{posting.provider}:{posting.provider_job_id}"

        if self._config.dedup_by_url and posting.url:
            normalized_url = posting.url.rstrip("/").lower()
            return f"url:{normalized_url}"

        if self._config.dedup_by_title_company_location:
            title = (posting.title or "").strip().lower()
            company = (posting.company.name or "").strip().lower()
            city = (posting.location.city or "").strip().lower()
            if title and company:
                return f"tcl:{title}|{company}|{city}"

        return None
