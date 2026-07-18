import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_posting import JobPosting
from app.schemas.job import JobCreate
from app.services.job_normalizer import JobNormalizer
from app.services.providers.base import RawJobData

logger = logging.getLogger(__name__)


class JobDeduplicator:
    """Removes duplicate job postings based on content hash."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.normalizer = JobNormalizer()

    async def deduplicate(self, raw_jobs: list[RawJobData]) -> tuple[list[JobCreate], int]:
        """Deduplicate a list of raw jobs. Returns (new_jobs, duplicates_removed)."""
        normalized = self.normalizer.normalize_batch(raw_jobs)
        return await self._filter_existing(normalized)

    async def _filter_existing(self, jobs: list[JobCreate]) -> tuple[list[JobCreate], int]:
        """Filter out jobs whose content_hash already exists in the database."""
        if not jobs:
            return [], 0

        hashes = [j.content_hash for j in jobs]

        stmt = select(JobPosting.content_hash).where(
            JobPosting.content_hash.in_(hashes)
        )
        result = await self.session.execute(stmt)
        existing_hashes = {row[0] for row in result.fetchall()}

        new_jobs = [j for j in jobs if j.content_hash not in existing_hashes]
        duplicates_removed = len(jobs) - len(new_jobs)

        if duplicates_removed:
            logger.info("Removed %d duplicate job(s)", duplicates_removed)

        return new_jobs, duplicates_removed

    async def mark_viewed(self, session: AsyncSession, job_id: str) -> None:
        from datetime import datetime

        stmt = select(JobPosting).where(JobPosting.id == job_id)
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()
        if job:
            job.viewed_at = datetime.utcnow()

    async def mark_applied(self, session: AsyncSession, job_id: str) -> None:
        from datetime import datetime

        stmt = select(JobPosting).where(JobPosting.id == job_id)
        result = await session.execute(stmt)
        job = result.scalar_one_or_none()
        if job:
            job.applied_at = datetime.utcnow()
