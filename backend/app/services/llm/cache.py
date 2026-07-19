import hashlib
import json
import logging
import time
from collections import OrderedDict

from app.schemas.llm import LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


class LLMCache:
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._cache: OrderedDict[str, tuple[float, LLMResponse]] = OrderedDict()

    def _make_key(self, request: LLMRequest) -> str:
        data = {
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "model": request.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        raw = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, request: LLMRequest) -> LLMResponse | None:
        key = self._make_key(request)
        entry = self._cache.get(key)
        if entry is None:
            return None
        timestamp, response = entry
        if time.monotonic() - timestamp > self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return response

    def set(self, request: LLMRequest, response: LLMResponse) -> None:
        key = self._make_key(request)
        self._cache[key] = (time.monotonic(), response)
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()

    def invalidate(self, request: LLMRequest) -> None:
        key = self._make_key(request)
        self._cache.pop(key, None)

    @property
    def size(self) -> int:
        return len(self._cache)
