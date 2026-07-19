import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ScheduleInterval(str, Enum):
    HOURLY = "hourly"
    EVERY_6_HOURS = "every_6_hours"
    EVERY_12_HOURS = "every_12_hours"
    DAILY = "daily"
    WEEKLY = "weekly"


INTERVAL_SECONDS = {
    ScheduleInterval.HOURLY: 3600,
    ScheduleInterval.EVERY_6_HOURS: 21600,
    ScheduleInterval.EVERY_12_HOURS: 43200,
    ScheduleInterval.DAILY: 86400,
    ScheduleInterval.WEEKLY: 604800,
}


@dataclass
class ScheduledJob:
    id: str
    name: str
    interval: ScheduleInterval
    last_run: datetime | None = None
    next_run: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    run_count: int = 0


class JobScheduler:
    """Schedule periodic background job searches using asyncio."""

    def __init__(self) -> None:
        self._jobs: dict[str, ScheduledJob] = {}
        self._handlers: dict[str, Callable[..., Awaitable]] = {}
        self._task: asyncio.Task | None = None

    def register(
        self,
        job_id: str,
        name: str,
        handler: Callable[..., Awaitable],
        interval: ScheduleInterval,
    ) -> ScheduledJob:
        job = ScheduledJob(id=job_id, name=name, interval=interval)
        self._jobs[job_id] = job
        self._handlers[job_id] = handler
        logger.info("Registered scheduled job: %s (%s)", job_id, interval.value)
        return job

    def unregister(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)
        self._handlers.pop(job_id, None)

    def get_job(self, job_id: str) -> ScheduledJob | None:
        return self._jobs.get(job_id)

    def list_jobs(self) -> list[ScheduledJob]:
        return list(self._jobs.values())

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._scheduler_loop())
            logger.info("JobScheduler started with %d job(s)", len(self._jobs))

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            import contextlib
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
            logger.info("JobScheduler stopped")

    async def trigger(self, job_id: str, **kwargs: Any) -> Any | None:
        handler = self._handlers.get(job_id)
        if not handler:
            logger.warning("No handler registered for job: %s", job_id)
            return None
        job = self._jobs.get(job_id)
        try:
            result = await handler(**kwargs)
            if job:
                job.last_run = datetime.utcnow()
                job.run_count += 1
            return result
        except Exception:
            logger.exception("Scheduled job %s failed", job_id)
            return None

    async def _scheduler_loop(self) -> None:
        while True:
            try:
                now = datetime.utcnow()
                for job_id, job in list(self._jobs.items()):
                    if not job.is_active:
                        continue
                    if now >= job.next_run:
                        logger.info("Running scheduled job: %s", job.name)
                        await self.trigger(job_id)
                        interval = INTERVAL_SECONDS.get(job.interval, 86400)
                        job.next_run = datetime.utcnow() + timedelta(seconds=interval)
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in scheduler loop")
                await asyncio.sleep(60)


_scheduler: JobScheduler | None = None


def get_job_scheduler() -> JobScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = JobScheduler()
    return _scheduler
