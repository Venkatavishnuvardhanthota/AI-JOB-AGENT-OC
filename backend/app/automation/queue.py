from __future__ import annotations

from datetime import datetime
from threading import Lock

from app.automation.exceptions import QueueFullError
from app.automation.schemas import AutomationJob, JobPriority, QueueItem, QueueStatistics


class AutomationQueue:
    def __init__(self, max_size: int = 1000) -> None:
        self._items: list[QueueItem] = []
        self._max_size = max_size
        self._paused = False
        self._lock = Lock()

    def enqueue(self, job: AutomationJob) -> QueueItem:
        with self._lock:
            if len(self._items) >= self._max_size:
                raise QueueFullError(message=f"Queue is full (max {self._max_size}).")
            item = QueueItem(
                job_id=job.id,
                priority=job.priority,
            )
            self._items.append(item)
            self._items.sort(key=lambda i: (-i.priority.value, i.enqueued_at))
            return item

    def dequeue(self) -> QueueItem | None:
        with self._lock:
            if self._paused or not self._items:
                return None
            now = datetime.utcnow()
            for i, item in enumerate(self._items):
                if item.scheduled_at is None or item.scheduled_at <= now:
                    return self._items.pop(i)
            return None

    def peek(self) -> QueueItem | None:
        with self._lock:
            if self._paused or not self._items:
                return None
            now = datetime.utcnow()
            for item in self._items:
                if item.scheduled_at is None or item.scheduled_at <= now:
                    return item
            return None

    def remove(self, job_id: str) -> bool:
        with self._lock:
            for i, item in enumerate(self._items):
                if item.job_id == job_id:
                    self._items.pop(i)
                    return True
            return False

    def update_priority(self, job_id: str, priority: JobPriority) -> bool:
        with self._lock:
            for item in self._items:
                if item.job_id == job_id:
                    item.priority = priority
                    self._items.sort(key=lambda i: (-i.priority.value, i.enqueued_at))
                    return True
            return False

    def pause(self) -> None:
        with self._lock:
            self._paused = True

    def resume(self) -> None:
        with self._lock:
            self._paused = False

    def is_paused(self) -> bool:
        with self._lock:
            return self._paused

    def get_queue(
        self,
        priority: JobPriority | None = None,
    ) -> list[QueueItem]:
        with self._lock:
            if priority is not None:
                return [i for i in self._items if i.priority == priority]
            return list(self._items)

    def get_statistics(self) -> QueueStatistics:
        with self._lock:
            stats = QueueStatistics()
            stats.total = len(self._items)
            stats.paused = self._paused
            for item in self._items:
                key = item.priority.name.lower()
                stats.by_priority[key] = stats.by_priority.get(key, 0) + 1
            if self._items:
                stats.oldest_enqueued = min(item.enqueued_at for item in self._items)
            return stats

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._items)

    @property
    def is_empty(self) -> bool:
        with self._lock:
            return len(self._items) == 0
