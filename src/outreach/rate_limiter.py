import asyncio
import logging
from src.config import Config

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """Limiteur à jetons : n requêtes max par fenêtre glissante."""

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max(1, max_requests)
        self.window = window_seconds
        self._timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = asyncio.get_event_loop().time()
            self._timestamps = [t for t in self._timestamps if now - t < self.window]
            if len(self._timestamps) >= self.max_requests:
                sleep_for = self.window - (now - self._timestamps[0])
                logger.debug(f"Rate limit atteint, pause {sleep_for:.1f}s")
                await asyncio.sleep(sleep_for)
                now = asyncio.get_event_loop().time()
                self._timestamps = [t for t in self._timestamps if now - t < self.window]
            self._timestamps.append(now)


# Instance globale pour l'outreach email
email_rate_limiter = TokenBucketRateLimiter(max_requests=10, window_seconds=60)