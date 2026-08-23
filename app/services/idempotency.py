from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.redis_client import get_redis
from app.core.config import settings
from app.models.webhook_event import WebhookEvent, EventStatus
from app.integrations.stripe.schemas import InternalStripeEvent


class IdempotencyService:
    """
    Doble capa de deduplicación: Redis (rápido) + PostgreSQL (persistente).
    Tema #4: idempotencia — garantiza que cada evento se procese exactamente una vez.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_redis(self, event_id: str) -> bool:
        """
        Primera capa: Redis con SETNX y TTL.
        Responde en microsegundos. Si la key ya existe → duplicado.
        """
        redis = await get_redis()
        key = f"idempotency:{event_id}"
        # SETNX: set if not exists. Retorna 1 si se creó (nuevo), 0 si ya existía (duplicado)
        created = await redis.set(key, "1", nx=True, ex=settings.IDEMPOTENCY_TTL_SECONDS)
        return not created  # True = es duplicado

    async def check_db(self, event_id: str) -> bool:
        """
        Segunda capa: PostgreSQL para eventos históricos (si Redis pierde datos).
        """
        result = await self.db.execute(
            select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        )
        return result.scalar_one_or_none() is not None

    async def persist_event(self, event: InternalStripeEvent) -> WebhookEvent:
        """Persiste el evento en PostgreSQL con estado 'received'."""
        webhook_event = WebhookEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            payload=event.model_dump(),
            status=EventStatus.RECEIVED,
        )
        self.db.add(webhook_event)
        await self.db.commit()
        await self.db.refresh(webhook_event)
        return webhook_event

    async def mark_processing(self, event_id: str) -> None:
        result = await self.db.execute(
            select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        )
        event = result.scalar_one_or_none()
        if event:
            event.status = EventStatus.PROCESSING
            await self.db.commit()

    async def mark_completed(self, event_id: str) -> None:
        from datetime import datetime, timezone
        result = await self.db.execute(
            select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        )
        event = result.scalar_one_or_none()
        if event:
            event.status = EventStatus.COMPLETED
            event.processed_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def mark_failed(self, event_id: str, error: str, increment_retry: bool = True) -> None:
        result = await self.db.execute(
            select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        )
        event = result.scalar_one_or_none()
        if event:
            event.status = EventStatus.FAILED
            event.error_message = error
            if increment_retry:
                event.retry_count += 1
            await self.db.commit()
