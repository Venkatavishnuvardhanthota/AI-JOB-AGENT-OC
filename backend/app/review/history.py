from __future__ import annotations

from threading import Lock

from app.review.schemas import ReviewRecord


class ReviewHistory:
    def __init__(self) -> None:
        self._entries: dict[str, list[ReviewRecord]] = {}
        self._lock = Lock()

    def add(self, review_id: str, entry: ReviewRecord) -> None:
        with self._lock:
            if review_id not in self._entries:
                self._entries[review_id] = []
            self._entries[review_id].append(entry)

    def get_history(self, review_id: str) -> list[ReviewRecord]:
        with self._lock:
            return list(self._entries.get(review_id, []))

    def clear(self, review_id: str | None = None) -> None:
        with self._lock:
            if review_id:
                self._entries.pop(review_id, None)
            else:
                self._entries.clear()

    def count(self, review_id: str) -> int:
        with self._lock:
            return len(self._entries.get(review_id, []))
