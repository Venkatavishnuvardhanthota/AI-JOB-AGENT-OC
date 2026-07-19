import logging
import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_posting import JobPosting
from app.repositories.job_posting import JobPostingRepository
from app.schemas.job import JobResponse, JobSearchRequest, JobSearchResult, ProviderStatus
from app.services.job_cache import TTLCache, get_job_cache
from app.services.job_deduplicator import JobDeduplicator
from app.services.job_normalizer import JobNormalizer
from app.services.providers.base import RawJobData
from app.services.providers.factory import get_provider_factory
from app.services.providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)


class JobSearchService:
    """Orchestrates job searches across providers with filtering, dedup, and storage."""

    def __init__(
        self,
        session: AsyncSession,
        registry: ProviderRegistry | None = None,
        cache: TTLCache | None = None,
    ) -> None:
        self.session = session
        self.registry = registry or self._build_registry()
        self.repo = JobPostingRepository(session)
        self.normalizer = JobNormalizer()
        self.deduplicator = JobDeduplicator(session)
        self.cache = cache or get_job_cache()

    def _build_registry(self) -> ProviderRegistry:
        factory = get_provider_factory()
        factory.create_all()
        return factory.registry

    async def search_all_providers(
        self, search_req: JobSearchRequest,
    ) -> dict[str, list[RawJobData]]:
        cache_key = f"search:{search_req.query}:{search_req.location}:{search_req.remote_only}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug("Returning cached search results for '%s'", search_req.query)
            return cached

        kwargs: dict[str, Any] = {}
        if search_req.location:
            kwargs["location"] = search_req.location
        if search_req.remote_only:
            kwargs["remote_only"] = True

        results = await self.registry.search_all(search_req.query, **kwargs)

        self.cache.set(cache_key, results, ttl_seconds=120)
        return results

    async def search_and_store(
        self,
        search_req: JobSearchRequest,
        user_id: uuid.UUID | None = None,
    ) -> JobSearchResult:
        provider_results = await self.search_all_providers(search_req)
        return await self._process_results(provider_results, search_req, user_id)

    async def _process_results(
        self,
        provider_results: dict[str, list[RawJobData]],
        search_req: JobSearchRequest,
        user_id: uuid.UUID | None = None,
    ) -> JobSearchResult:
        all_raw: list[RawJobData] = []
        provider_statuses: list[ProviderStatus] = []

        for provider_name, jobs in provider_results.items():
            status = ProviderStatus(name=provider_name, enabled=True, jobs_found=len(jobs))
            all_raw.extend(jobs)
            provider_statuses.append(status)

        if not all_raw:
            return JobSearchResult(jobs=[], providers=provider_statuses, total_new=0, duplicates_removed=0)

        normalized = self.normalizer.normalize_batch(all_raw)

        if search_req.salary_min is not None:
            normalized = [j for j in normalized if j.salary_max is None or j.salary_max >= search_req.salary_min]

        if search_req.salary_max is not None:
            normalized = [j for j in normalized if j.salary_min is None or j.salary_min <= search_req.salary_max]

        if search_req.job_type:
            jt = search_req.job_type.lower()
            normalized = [j for j in normalized if j.job_type and jt in j.job_type.lower()]

        if search_req.sources:
            sources_set = set(search_req.sources)
            normalized = [j for j in normalized if j.source in sources_set]

        new_jobs, duplicates = await self.deduplicator.filter_existing(normalized)

        saved_responses: list[JobResponse] = []
        if new_jobs:
            for job in new_jobs:
                data = job.model_dump()
                if user_id:
                    data["user_id"] = user_id
                instance = await self.repo.create(**data)
                saved_responses.append(JobResponse.model_validate(instance))
        else:
            if user_id:
                for raw_job in all_raw:
                    normalized_job = self.normalizer.normalize(raw_job)
                    data = normalized_job.model_dump()
                    data["user_id"] = user_id
                    existing = await self.repo.get_by_hash(data["content_hash"])
                    if existing:
                        saved_responses.append(JobResponse.model_validate(existing))
            else:
                pass

        return JobSearchResult(
            jobs=saved_responses,
            providers=provider_statuses,
            total_new=len(saved_responses),
            duplicates_removed=duplicates,
        )

    async def list_jobs(
        self,
        *,
        query: str = "",
        location: str | None = None,
        remote_only: bool = False,
        sources: list[str] | None = None,
        salary_min: float | None = None,
        salary_max: float | None = None,
        job_type: str | None = None,
        skills: list[str] | None = None,
        is_active: bool | None = None,
        user_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[JobPosting], int]:
        skip = (page - 1) * page_size
        return await self.repo.search(
            query=query,
            location=location,
            remote_only=remote_only,
            sources=sources,
            salary_min=salary_min,
            salary_max=salary_max,
            job_type=job_type,
            skills=skills,
            is_active=is_active,
            user_id=user_id,
            skip=skip,
            limit=page_size,
        )

    async def get_job(self, job_id: uuid.UUID) -> JobPosting | None:
        return await self.repo.get(job_id)

    async def update_job(self, job_id: uuid.UUID, **kwargs: Any) -> JobPosting | None:
        return await self.repo.update(job_id, **kwargs)

    async def mark_viewed(self, job_id: uuid.UUID) -> JobPosting | None:
        return await self.repo.mark_viewed(job_id)

    async def mark_applied(self, job_id: uuid.UUID) -> JobPosting | None:
        return await self.repo.mark_applied(job_id)

    async def get_saved_jobs(
        self,
        user_id: uuid.UUID,
        *,
        viewed: bool | None = None,
        applied: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[JobPosting], int]:
        skip = (page - 1) * page_size
        return await self.repo.list_saved(
            user_id, viewed=viewed, applied=applied, skip=skip, limit=page_size,
        )

    async def get_stats(self, user_id: uuid.UUID | None = None) -> dict:
        return await self.repo.get_stats(user_id=user_id)

    async def delete_job(self, job_id: uuid.UUID) -> bool:
        return await self.repo.delete(job_id)

    async def invalidate_cache(self, query: str | None = None) -> None:
        if query:
            self.cache.delete(f"search:{query}")
        else:
            self.cache.invalidate_by_prefix("search:")

    @staticmethod
    def search_request_to_params(req: JobSearchRequest) -> dict:
        return {
            "query": req.query,
            "location": req.location,
            "remote_only": req.remote_only,
            "sources": req.sources,
            "salary_min": req.salary_min,
            "salary_max": req.salary_max,
            "job_type": req.job_type,
            "skills": req.skills,
            "page": req.page,
            "page_size": req.page_size,
        }
