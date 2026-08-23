from app.tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=120,
    name="app.tasks.hubspot_tasks.sync_to_hubspot",
)
def sync_to_hubspot(self, event_id: str, event_type: str, payload: dict):
    """
    Sincroniza un evento Stripe a HubSpot.
    Implementación completa en Fase 4 del plan.
    TODO: instanciar sync_orchestrator y ejecutar el pipeline.
    """
    # TODO Fase 4: implementar sync_orchestrator.run(event_id, event_type, payload)
    pass
