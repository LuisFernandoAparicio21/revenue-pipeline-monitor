import time
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import get_redis
from app.core.config import settings


class HealthChecker:
    """
    Verifica el estado en tiempo real de cada integración.
    Tema #9: observabilidad y troubleshooting sistemático.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_all(self) -> dict:
        results = {}
        for integration in ["hubspot", "stripe", "redis", "database"]:
            results[integration] = await self.check_one(integration)
        return {"status": "ok", "integrations": results}

    async def check_one(self, integration: str) -> dict:
        checkers = {
            "hubspot": self._check_hubspot,
            "stripe": self._check_stripe,
            "redis": self._check_redis,
            "database": self._check_database,
        }
        checker = checkers.get(integration)
        if not checker:
            return {"healthy": False, "error": f"Integración '{integration}' no reconocida"}
        return await checker()

    async def _check_hubspot(self) -> dict:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                # Llamada liviana: lista de owners con limit=1
                response = await client.get(
                    f"{settings.HUBSPOT_API_BASE_URL}/crm/v3/owners",
                    params={"limit": 1},
                    headers={"Authorization": f"Bearer placeholder"},
                )
                latency_ms = int((time.time() - start) * 1000)
                # 401 es OK — significa que HubSpot responde (el token puede estar vencido)
                reachable = response.status_code in (200, 401)
                return {"healthy": reachable, "latency_ms": latency_ms, "status_code": response.status_code}
        except Exception as e:
            return {"healthy": False, "error": str(e), "latency_ms": int((time.time() - start) * 1000)}

    async def _check_stripe(self) -> dict:
        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    "https://api.stripe.com/v1/balance",
                    headers={"Authorization": f"Bearer {settings.STRIPE_SECRET_KEY}"},
                )
                latency_ms = int((time.time() - start) * 1000)
                return {"healthy": response.status_code == 200, "latency_ms": latency_ms}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def _check_redis(self) -> dict:
        start = time.time()
        try:
            redis = await get_redis()
            await redis.ping()
            return {"healthy": True, "latency_ms": int((time.time() - start) * 1000)}
        except Exception as e:
            return {"healthy": False, "error": str(e)}

    async def _check_database(self) -> dict:
        start = time.time()
        try:
            await self.db.execute(
                __import__("sqlalchemy", fromlist=["text"]).text("SELECT 1")
            )
            return {"healthy": True, "latency_ms": int((time.time() - start) * 1000)}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
