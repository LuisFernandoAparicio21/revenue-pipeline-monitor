import time
import asyncio
from app.core.redis_client import get_redis
from app.core.config import settings

BUCKET_KEY = "hubspot:rate_limit:bucket"
LAST_REFILL_KEY = "hubspot:rate_limit:last_refill"


class HubSpotRateLimiter:
    """
    Token bucket en Redis para respetar los límites de HubSpot.
    Tema #7: rate limiting distribuido con parsing de headers 429.
    """

    def __init__(self):
        self.rate = settings.HUBSPOT_REQUESTS_PER_SECOND
        self.capacity = self.rate * 2  # burst máximo = 2 segundos de requests

    async def acquire(self) -> None:
        """Espera hasta que haya un token disponible."""
        redis = await get_redis()

        while True:
            await self._refill(redis)
            tokens = await redis.get(BUCKET_KEY)

            if tokens and int(tokens) > 0:
                await redis.decr(BUCKET_KEY)
                return

            await asyncio.sleep(1.0 / self.rate)

    async def backoff_on_429(self, retry_after: int | None = None) -> None:
        """
        Cuando HubSpot responde 429, vacía el bucket y espera.
        Tema #7: parseo del header Retry-After.
        """
        redis = await get_redis()
        await redis.set(BUCKET_KEY, 0)

        wait_seconds = retry_after if retry_after else 10
        await asyncio.sleep(wait_seconds)

    async def _refill(self, redis) -> None:
        now = time.time()
        last_refill = await redis.get(LAST_REFILL_KEY)
        last_refill = float(last_refill) if last_refill else now

        elapsed = now - last_refill
        tokens_to_add = int(elapsed * self.rate)

        if tokens_to_add > 0:
            current = await redis.get(BUCKET_KEY)
            current = int(current) if current else self.capacity
            new_total = min(self.capacity, current + tokens_to_add)
            await redis.set(BUCKET_KEY, new_total)
            await redis.set(LAST_REFILL_KEY, now)
