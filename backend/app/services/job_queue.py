import asyncio
import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Any = None
    error: str | None = None


class JobQueue:
    """Simple in-process async task queue for background job processing."""

    def __init__(self, max_concurrent: int = 2, max_retained_tasks: int = 100) -> None:
        self._queue: asyncio.Queue[tuple[str, Callable[..., Awaitable], dict]] = asyncio.Queue()
        self._tasks: dict[str, Task] = {}
        self._max_concurrent = max_concurrent
        self._max_retained_tasks = max_retained_tasks
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._worker_task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("JobQueue worker started (max_concurrent=%d)", self._max_concurrent)

    async def stop(self) -> None:
        if self._worker_task:
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task
            self._worker_task = None
            logger.info("JobQueue worker stopped")

    async def enqueue(self, name: str, fn: Callable[..., Awaitable], **kwargs: Any) -> str:
        task_id = str(uuid.uuid4())
        task = Task(id=task_id, name=name)
        self._tasks[task_id] = task
        await self._queue.put((task_id, fn, kwargs))
        logger.debug("Enqueued task %s: %s", task_id, name)
        self._cleanup_old_tasks()
        return task_id

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def get_tasks(self, status: TaskStatus | None = None, limit: int = 20) -> list[Task]:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    def _cleanup_old_tasks(self) -> None:
        if len(self._tasks) <= self._max_retained_tasks:
            return
        completed = [
            t for t in self._tasks.values()
            if t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
        ]
        completed.sort(key=lambda t: t.completed_at or t.created_at)
        remove_count = len(self._tasks) - self._max_retained_tasks
        for t in completed[:remove_count]:
            self._tasks.pop(t.id, None)

    async def _worker_loop(self) -> None:
        while True:
            try:
                task_id, fn, kwargs = await self._queue.get()
                async with self._semaphore:
                    await self._execute_task(task_id, fn, **kwargs)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Unexpected error in job queue worker")

    async def _execute_task(self, task_id: str, fn: Callable[..., Awaitable], **kwargs: Any) -> None:
        task = self._tasks.get(task_id)
        if not task:
            return
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc)
        try:
            result = await fn(**kwargs)
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.now(timezone.utc)
            logger.info("Task %s completed successfully", task_id)
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now(timezone.utc)
            logger.exception("Task %s failed: %s", task_id, e)


import contextlib

_job_queue: JobQueue | None = None


def get_job_queue() -> JobQueue:
    global _job_queue
    if _job_queue is None:
        _job_queue = JobQueue()
    return _job_queue
