import asyncio
import time


class TokenBucketRateLimiter:
    """Token bucket rate limiter for per-provider request throttling."""

    def __init__(self, rate: float, burst: int | None = None) -> None:
        self.rate = rate
        self.burst = burst or max(1, int(rate))
        self.tokens = float(self.burst)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> float:
        """Wait for a token and return the wait time in seconds."""
        async with self._lock:
            self._refill()
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return 0.0
            wait = (1.0 - self.tokens) / self.rate
            self.tokens = 0.0
            self.last_refill = time.monotonic()
        await asyncio.sleep(wait)
        return wait

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(float(self.burst), self.tokens + elapsed * self.rate)
        self.last_refill = now


class RateLimiterRegistry:
    """Registry of rate limiters keyed by provider name."""

    def __init__(self) -> None:
        self._limiters: dict[str, TokenBucketRateLimiter] = {}

    def get(self, provider: str, rate: float = 1.0, burst: int | None = None) -> TokenBucketRateLimiter:
        if provider not in self._limiters:
            self._limiters[provider] = TokenBucketRateLimiter(rate, burst)
        return self._limiters[provider]

    def remove(self, provider: str) -> None:
        self._limiters.pop(provider, None)


rate_limiter_registry = RateLimiterRegistry()
