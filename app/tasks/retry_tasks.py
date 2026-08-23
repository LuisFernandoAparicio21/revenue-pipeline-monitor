from app.tasks.celery_app import celery_app
from app.tasks.stripe_tasks import process_stripe_event


@celery_app.task(name="app.tasks.retry_tasks.replay_failed_event")
def replay_failed_event(event_id: str):
    """
    Re-procesa un evento fallido desde el endpoint de admin.
    Tema #9: herramienta de recuperación manual de errores.
    TODO: cargar el payload desde DB y re-encolar en process_stripe_event.
    """
    # TODO Fase 6: cargar evento de DB y re-encolar
    pass
