from __future__ import annotations

import asyncio
import time


class TokenBucketRateLimiter:
    def __init__(self, rate: float, burst: int) -> None:
        if rate <= 0:
            raise ValueError("Rate must be positive")
        if burst < 1:
            raise ValueError("Burst must be at least 1")
        self._rate = rate
        self._burst = burst
        self._tokens = float(burst)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait_time = (1.0 - self._tokens) / self._rate

            await asyncio.sleep(wait_time)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(float(self._burst), self._tokens + elapsed * self._rate)
        self._last_refill = now
