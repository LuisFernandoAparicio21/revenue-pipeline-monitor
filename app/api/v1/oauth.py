from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import secrets

from app.core.database import get_db
from app.core.config import settings
from app.integrations.hubspot.auth import HubSpotAuth

router = APIRouter()

# Estado temporal para CSRF protection (en producción usar Redis)
_oauth_states: set[str] = set()


@router.get("/hubspot/authorize")
async def hubspot_authorize():
    """
    Inicia el flujo Authorization Code de HubSpot.
    Tema #1: OAuth 2.0 Authorization Code Flow.
    """
    state = secrets.token_urlsafe(32)
    _oauth_states.add(state)

    auth_url = (
        f"https://app.hubspot.com/oauth/authorize"
        f"?client_id={settings.HUBSPOT_CLIENT_ID}"
        f"&redirect_uri={settings.HUBSPOT_REDIRECT_URI}"
        f"&scope={settings.HUBSPOT_SCOPES.replace(' ', '%20')}"
        f"&state={state}"
    )
    return RedirectResponse(url=auth_url)


@router.get("/hubspot/callback")
async def hubspot_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Callback del flujo OAuth. Intercambia el code por access_token + refresh_token.
    Tema #1: refresh token management + almacenamiento seguro.
    """
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="State inválido — posible CSRF")
    _oauth_states.discard(state)

    auth = HubSpotAuth(db)
    token_data = await auth.exchange_code(code)

    return {
        "status": "authorized",
        "portal_id": token_data.get("hub_id"),
        "expires_in": token_data.get("expires_in"),
        "scope": token_data.get("scope"),
    }


@router.post("/hubspot/refresh")
async def hubspot_refresh_token(db: AsyncSession = Depends(get_db)):
    """
    Refresca el access token manualmente.
    Tema #1: refresh token flow.
    """
    auth = HubSpotAuth(db)
    token = await auth.get_valid_token()
    return {"status": "refreshed", "expires_at": str(token.expires_at)}
