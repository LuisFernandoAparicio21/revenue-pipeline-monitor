from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_stripe_signature, WebhookSignatureError
from app.services.idempotency import IdempotencyService
from app.integrations.stripe.parser import parse_stripe_event
from app.tasks.stripe_tasks import process_stripe_event

router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Receptor de webhooks de Stripe.
    Tema #2: HMAC-SHA256 + async + idempotencia
    Responde en < 200ms, procesa en background.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    # [1] Validar firma HMAC-SHA256
    try:
        verify_stripe_signature(payload, sig_header)
    except WebhookSignatureError as e:
        raise HTTPException(status_code=401, detail=str(e))

    # [2] Parsear evento
    try:
        event = parse_stripe_event(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # [3] Verificar idempotencia (capa rápida Redis)
    idempotency = IdempotencyService(db)
    is_duplicate = await idempotency.check_redis(event.event_id)
    if is_duplicate:
        return {"received": True, "status": "duplicate", "event_id": event.event_id}

    # [4] Persistir evento y encolar procesamiento async
    await idempotency.persist_event(event)
    process_stripe_event.delay(event.event_id, event.event_type, event.model_dump())

    return {"received": True, "status": "queued", "event_id": event.event_id}
