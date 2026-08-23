from app.tasks.celery_app import celery_app
from app.tasks.hubspot_tasks import sync_to_hubspot


@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    name="app.tasks.stripe_tasks.process_stripe_event",
)
def process_stripe_event(self, event_id: str, event_type: str, payload: dict):
    """
    Task principal de procesamiento de eventos Stripe.
    Tema #2: procesamiento async fuera del path HTTP.
    Tema #3: retry con backoff configurado en Celery.
    """
    try:
        sync_to_hubspot.apply_async(
            args=[event_id, event_type, payload],
            queue="hubspot_sync",
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
