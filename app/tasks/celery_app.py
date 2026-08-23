from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "revenue_pipeline",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.stripe_tasks",
        "app.tasks.hubspot_tasks",
        "app.tasks.enrichment_tasks",
        "app.tasks.retry_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_max_retries=settings.CELERY_TASK_MAX_RETRIES,
    task_default_retry_delay=settings.CELERY_TASK_DEFAULT_RETRY_DELAY,
    task_routes={
        "app.tasks.stripe_tasks.*": {"queue": "webhooks"},
        "app.tasks.hubspot_tasks.*": {"queue": "hubspot_sync"},
        "app.tasks.enrichment_tasks.*": {"queue": "llm_enrichment"},
        "app.tasks.retry_tasks.*": {"queue": "webhooks"},
    },
)
