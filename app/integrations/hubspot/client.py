import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.hubspot.auth import HubSpotAuth
from app.integrations.hubspot.rate_limiter import HubSpotRateLimiter
from app.utils.backoff import retry_on_rate_limit, retry_on_server_error

rate_limiter = HubSpotRateLimiter()


class HubSpotClient:
    """
    Cliente HTTP base para la API de HubSpot.
    Tema #3: retry + exponential backoff.
    Tema #7: rate limiting + 429 handling.
    """

    def __init__(self, db: AsyncSession):
        self.base_url = settings.HUBSPOT_API_BASE_URL
        self.auth = HubSpotAuth(db)

    async def _get_headers(self) -> dict:
        token = await self.auth.get_access_token_string()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @retry_on_server_error
    async def get(self, path: str, params: dict | None = None) -> dict:
        await rate_limiter.acquire()
        headers = await self._get_headers()

        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
            response = await client.get(
                f"{self.base_url}{path}",
                headers=headers,
                params=params,
            )
            return await self._handle_response(response)

    @retry_on_server_error
    async def post(self, path: str, body: dict) -> dict:
        await rate_limiter.acquire()
        headers = await self._get_headers()

        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{self.base_url}{path}",
                headers=headers,
                json=body,
            )
            return await self._handle_response(response)

    @retry_on_server_error
    async def patch(self, path: str, body: dict) -> dict:
        await rate_limiter.acquire()
        headers = await self._get_headers()

        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT_SECONDS) as client:
            response = await client.patch(
                f"{self.base_url}{path}",
                headers=headers,
                json=body,
            )
            return await self._handle_response(response)

    async def _handle_response(self, response: httpx.Response) -> dict:
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 10))
            await rate_limiter.backoff_on_429(retry_after)
            raise httpx.HTTPStatusError(
                "Rate limit alcanzado (429)",
                request=response.request,
                response=response,
            )

        response.raise_for_status()
        return response.json() if response.content else {}
