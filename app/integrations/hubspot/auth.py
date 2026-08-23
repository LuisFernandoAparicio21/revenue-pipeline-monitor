from datetime import datetime, timezone, timedelta
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.oauth_token import OAuthToken
from app.utils.crypto import encrypt_token, decrypt_token


TOKEN_REFRESH_BUFFER_SECONDS = 300  # Refrescar si quedan menos de 5 min


class HubSpotAuth:
    """
    Gestión completa de tokens OAuth 2.0 con HubSpot.
    Tema #1: Authorization Code flow + refresh token automático.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.token_url = "https://api.hubapi.com/oauth/v1/token"

    async def exchange_code(self, code: str) -> dict:
        """Intercambia el authorization code por access_token + refresh_token."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.HUBSPOT_CLIENT_ID,
                    "client_secret": settings.HUBSPOT_CLIENT_SECRET,
                    "redirect_uri": settings.HUBSPOT_REDIRECT_URI,
                    "code": code,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            token_data = response.json()

        await self._save_token(token_data)
        return token_data

    async def get_valid_token(self) -> OAuthToken:
        """
        Devuelve un token válido. Si está próximo a expirar, lo refresca automáticamente.
        Tema #1: refresh token flow automático.
        """
        result = await self.db.execute(
            select(OAuthToken)
            .where(OAuthToken.integration == "hubspot")
            .order_by(OAuthToken.created_at.desc())
        )
        token = result.scalar_one_or_none()

        if not token:
            raise ValueError("No hay token de HubSpot. Completa el flujo OAuth primero.")

        now = datetime.now(timezone.utc)
        expires_soon = token.expires_at - timedelta(seconds=TOKEN_REFRESH_BUFFER_SECONDS)

        if now >= expires_soon:
            token = await self._refresh_token(token)

        return token

    async def get_access_token_string(self) -> str:
        token = await self.get_valid_token()
        return decrypt_token(token.access_token)

    async def _refresh_token(self, token: OAuthToken) -> OAuthToken:
        """Refresca el access token usando el refresh token almacenado."""
        refresh_token = decrypt_token(token.refresh_token)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_url,
                data={
                    "grant_type": "refresh_token",
                    "client_id": settings.HUBSPOT_CLIENT_ID,
                    "client_secret": settings.HUBSPOT_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            new_token_data = response.json()

        return await self._save_token(new_token_data, existing_id=token.id)

    async def _save_token(self, token_data: dict, existing_id: str | None = None) -> OAuthToken:
        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        if existing_id:
            result = await self.db.execute(
                select(OAuthToken).where(OAuthToken.id == existing_id)
            )
            token = result.scalar_one()
            token.access_token = encrypt_token(token_data["access_token"])
            if "refresh_token" in token_data:
                token.refresh_token = encrypt_token(token_data["refresh_token"])
            token.expires_at = expires_at
            token.scope = token_data.get("scope")
        else:
            token = OAuthToken(
                integration="hubspot",
                grant_type="authorization_code",
                access_token=encrypt_token(token_data["access_token"]),
                refresh_token=encrypt_token(token_data.get("refresh_token", "")),
                expires_at=expires_at,
                scope=token_data.get("scope"),
                portal_id=str(token_data.get("hub_id", "")),
            )
            self.db.add(token)

        await self.db.commit()
        await self.db.refresh(token)
        return token
