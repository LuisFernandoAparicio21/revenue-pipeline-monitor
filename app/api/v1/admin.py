from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.webhook_event import WebhookEvent, EventStatus
from app.tasks.retry_tasks import replay_failed_event

router = APIRouter()


@router.get("/events")
async def list_events(
    status: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """
    Lista eventos recibidos por estado.
    Tema #9: herramienta de diagnóstico y troubleshooting.
    """
    query = select(WebhookEvent).order_by(WebhookEvent.received_at.desc()).limit(limit)
    if status:
        query = query.where(WebhookEvent.status == status)

    result = await db.execute(query)
    events = result.scalars().all()
    return [
        {
            "event_id": e.event_id,
            "event_type": e.event_type,
            "status": e.status,
            "received_at": e.received_at,
            "retry_count": e.retry_count,
            "error_message": e.error_message,
        }
        for e in events
    ]


@router.post("/events/{event_id}/replay")
async def replay_event(event_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fuerza el re-procesamiento de un evento fallido.
    Tema #9: replay manual para recuperación de errores.
    """
    result = await db.execute(
        select(WebhookEvent).where(WebhookEvent.event_id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    if event.status not in (EventStatus.FAILED, EventStatus.RECEIVED):
        raise HTTPException(
            status_code=400,
            detail=f"Solo se pueden replay eventos en estado 'failed' o 'received'. Estado actual: {event.status}",
        )

    replay_failed_event.delay(event_id)
    return {"status": "replay_queued", "event_id": event_id}
