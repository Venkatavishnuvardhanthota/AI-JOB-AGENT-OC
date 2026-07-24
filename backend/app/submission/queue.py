from __future__ import annotations

from datetime import datetime
from threading import Lock

from app.submission.schemas import (
    QueueItem,
    QueueStatistics,
    SubmissionPriority,
    SubmissionRecord,
    SubmissionState,
)


class SubmissionQueue:
    def __init__(self) -> None:
        self._items: list[QueueItem] = []
        self._lock = Lock()

    def enqueue(
        self,
        record: SubmissionRecord,
        scheduled_at: datetime | None = None,
    ) -> QueueItem:
        item = QueueItem(
            submission_id=record.id,
            priority=record.priority,
            scheduled_at=scheduled_at,
        )
        with self._lock:
            self._items.append(item)
            self._items.sort(key=lambda i: (-i.priority.value, i.enqueued_at))
        record.state = SubmissionState.QUEUED
        record.updated_at = datetime.utcnow()
        return item

    def dequeue(self) -> QueueItem | None:
        with self._lock:
            if not self._items:
                return None

            now = datetime.utcnow()
            for i, item in enumerate(self._items):
                if item.scheduled_at is None or item.scheduled_at <= now:
                    return self._items.pop(i)
            return None

    def peek(self) -> QueueItem | None:
        with self._lock:
            if not self._items:
                return None
            now = datetime.utcnow()
            for item in self._items:
                if item.scheduled_at is None or item.scheduled_at <= now:
                    return item
            return None

    def remove(self, submission_id: str) -> bool:
        with self._lock:
            for i, item in enumerate(self._items):
                if item.submission_id == submission_id:
                    self._items.pop(i)
                    return True
            return False

    def update_priority(
        self,
        submission_id: str,
        priority: SubmissionPriority,
    ) -> bool:
        with self._lock:
            for item in self._items:
                if item.submission_id == submission_id:
                    item.priority = priority
                    self._items.sort(key=lambda i: (-i.priority.value, i.enqueued_at))
                    return True
            return False

    def get_queue(
        self,
        priority: SubmissionPriority | None = None,
    ) -> list[QueueItem]:
        with self._lock:
            if priority is not None:
                return [i for i in self._items if i.priority == priority]
            return list(self._items)

    def get_statistics(
        self,
        records: dict[str, SubmissionRecord] | None = None,
    ) -> QueueStatistics:
        with self._lock:
            stats = QueueStatistics()
            stats.total = len(self._items)

            for item in self._items:
                key = item.priority.name.lower()
                stats.by_priority[key] = stats.by_priority.get(key, 0) + 1

            if records:
                for item in self._items:
                    record = records.get(item.submission_id)
                    if record:
                        key = record.state.value
                        stats.by_state[key] = stats.by_state.get(key, 0) + 1

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
