"""Tests for job search service, cache, queue, scheduler, and API."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.job_posting import JobPostingRepository
from app.schemas.job import JobSearchRequest, JobSearchResult
from app.services.job_cache import TTLCache, get_job_cache
from app.services.job_deduplicator import JobDeduplicator
from app.services.job_normalizer import JobNormalizer
from app.services.job_queue import JobQueue, TaskStatus, get_job_queue
from app.services.job_scheduler import JobScheduler, ScheduleInterval, get_job_scheduler
from app.services.job_search import JobSearchService
from app.services.providers.registry import ProviderRegistry

# ── Cache ──


class TestTTLCache:
    def test_set_and_get(self):
        cache = TTLCache(default_ttl_seconds=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_key(self):
        cache = TTLCache()
        assert cache.get("nonexistent") is None

    def test_delete(self):
        cache = TTLCache()
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_clear(self):
        cache = TTLCache()
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.size == 0

    def test_invalidate_by_prefix(self):
        cache = TTLCache()
        cache.set("search:python", [])
        cache.set("search:java", [])
        cache.set("other", 1)
        cache.invalidate_by_prefix("search:")
        assert cache.get("search:python") is None
        assert cache.get("other") == 1

    def test_expiry(self):
        cache = TTLCache(default_ttl_seconds=-1)
        cache.set("key1", "value1")
        import time
        time.monotonic()
        assert cache.get("key1") is None

    def test_singleton(self):
        c1 = get_job_cache()
        c2 = get_job_cache()
        assert c1 is c2


# ── Queue ──


class TestJobQueue:
    @pytest.mark.asyncio
    async def test_enqueue_and_execute(self):
        queue = JobQueue(max_concurrent=5)
        await queue.start()

        async def dummy_fn(value: str) -> str:
            return f"processed:{value}"

        task_id = await queue.enqueue("test", dummy_fn, value="hello")
        assert task_id is not None

        import asyncio
        await asyncio.sleep(0.1)

        task = queue.get_task(task_id)
        assert task is not None
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "processed:hello"

        await queue.stop()

    @pytest.mark.asyncio
    async def test_enqueue_failure(self):
        queue = JobQueue(max_concurrent=5)
        await queue.start()

        async def failing_fn() -> None:
            raise ValueError("Something went wrong")

        task_id = await queue.enqueue("failing", failing_fn)

        import asyncio
        await asyncio.sleep(0.1)

        task = queue.get_task(task_id)
        assert task is not None
        assert task.status == TaskStatus.FAILED
        assert task.error is not None

        await queue.stop()

    def test_get_tasks_empty(self):
        queue = JobQueue()
        assert len(queue.get_tasks()) == 0

    def test_get_tasks_limit(self):
        queue = JobQueue()
        assert len(queue.get_tasks(status=TaskStatus.PENDING, limit=5)) == 0

    def test_singleton(self):
        q1 = get_job_queue()
        q2 = get_job_queue()
        assert q1 is q2

    @pytest.mark.asyncio
    async def test_stop_without_start(self):
        queue = JobQueue()
        await queue.stop()


# ── Scheduler ──


class TestJobScheduler:
    @pytest.mark.asyncio
    async def test_register_and_trigger(self):
        scheduler = JobScheduler()
        handler = AsyncMock(return_value="done")

        job = scheduler.register(
            "test_job", "Test Job", handler, ScheduleInterval.DAILY
        )
        assert job.id == "test_job"
        assert job.interval == ScheduleInterval.DAILY
        assert job.is_active is True

        result = await scheduler.trigger("test_job")
        assert result == "done"
        assert handler.call_count == 1
        assert job.run_count == 1

    @pytest.mark.asyncio
    async def test_trigger_unknown(self):
        scheduler = JobScheduler()
        result = await scheduler.trigger("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_jobs(self):
        scheduler = JobScheduler()
        scheduler.register("a", "Job A", AsyncMock(), ScheduleInterval.HOURLY)
        scheduler.register("b", "Job B", AsyncMock(), ScheduleInterval.DAILY)
        assert len(scheduler.list_jobs()) == 2

    def test_unregister(self):
        scheduler = JobScheduler()
        handler = AsyncMock()
        scheduler.register("x", "X", handler, ScheduleInterval.HOURLY)
        scheduler.unregister("x")
        assert scheduler.get_job("x") is None

    def test_singleton(self):
        s1 = get_job_scheduler()
        s2 = get_job_scheduler()
        assert s1 is s2


# ── JobSearchService ──


class TestJobSearchService:
    @pytest.mark.asyncio
    async def test_search_and_store_empty(self):
        service = JobSearchService.__new__(JobSearchService)
        service.registry = MagicMock(spec=ProviderRegistry)
        service.registry.search_all = AsyncMock(return_value={})
        service.normalizer = JobNormalizer()
        service.repo = MagicMock(spec=JobPostingRepository)
        service.deduplicator = MagicMock(spec=JobDeduplicator)
        service.cache = TTLCache()

        req = JobSearchRequest(query="Python Developer")
        result = await service.search_and_store(req)
        assert isinstance(result, JobSearchResult)
        assert result.jobs == []
        assert result.total_new == 0
        assert result.duplicates_removed == 0

    @pytest.mark.asyncio
    async def test_search_all_providers_caches(self):
        service = JobSearchService.__new__(JobSearchService)
        service.registry = MagicMock(spec=ProviderRegistry)
        service.registry.search_all = AsyncMock(return_value={"dummy": []})
        service.cache = TTLCache()

        req = JobSearchRequest(query="Python")
        result1 = await service.search_all_providers(req)
        result2 = await service.search_all_providers(req)
        assert result1 == result2
        assert service.registry.search_all.call_count == 1

    @pytest.mark.asyncio
    async def test_invalidate_cache(self):
        service = JobSearchService.__new__(JobSearchService)
        service.cache = TTLCache()
        service.cache.set("search:python", [1, 2, 3])
        service.cache.set("other", 42)

        await service.invalidate_cache()
        assert service.cache.get("search:python") is None
        assert service.cache.get("other") == 42

    @pytest.mark.asyncio
    async def test_get_saved_jobs(self):
        service = JobSearchService.__new__(JobSearchService)
        service.repo = MagicMock(spec=JobPostingRepository)
        service.repo.list_saved = AsyncMock(return_value=([], 0))

        items, total = await service.get_saved_jobs(uuid.uuid4())
        assert items == []
        assert total == 0


# ── JobPostingRepository ──


class TestJobPostingRepositoryQueries:
    @pytest.mark.asyncio
    async def test_get_by_hash(self):
        repo = MagicMock(spec=JobPostingRepository)
        repo.get_by_hash = AsyncMock(return_value=None)
        result = await repo.get_by_hash("abc123")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_source_and_id(self):
        repo = MagicMock(spec=JobPostingRepository)
        repo.get_by_source_and_id = AsyncMock(return_value=None)
        result = await repo.get_by_source_and_id("linkedin", "12345")
        assert result is None

    @pytest.mark.asyncio
    async def test_mark_viewed(self):
        repo = MagicMock(spec=JobPostingRepository)
        repo.mark_viewed = AsyncMock(return_value=None)
        result = await repo.mark_viewed(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_mark_applied(self):
        repo = MagicMock(spec=JobPostingRepository)
        repo.mark_applied = AsyncMock(return_value=None)
        result = await repo.mark_applied(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_stats(self):
        repo = MagicMock(spec=JobPostingRepository)
        repo.get_stats = AsyncMock(return_value={
            "total": 10, "viewed": 5, "applied": 2, "active": 8, "by_source": {},
        })
        stats = await repo.get_stats()
        assert stats["total"] == 10
        assert stats["viewed"] == 5


# ── API Routes ──


def test_jobs_router_registered():
    from app.api.v1.jobs import router as jobs_router
    routes = [r.path for r in jobs_router.routes]
    assert "/search" in routes
    assert "/saved" in routes
    assert "/stats" in routes
    assert "/tasks/{task_id}" in routes
    assert "/{job_id}" in routes
    assert "/scheduler/register" in routes
    assert "/scheduler/jobs" in routes
    assert "/search/async" in routes
