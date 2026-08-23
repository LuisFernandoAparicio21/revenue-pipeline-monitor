from app.tasks.celery_app import celery_app


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,
    name="app.tasks.enrichment_tasks.enrich_contact",
)
def enrich_contact(self, email: str, hubspot_contact_id: str, payment_amount_cents: int = 0):
    """
    Enriquece un contacto nuevo con LLM en cola separada (baja prioridad).
    Tema #5: function calling en background.
    TODO Fase 5: instanciar ContactEnrichmentAgent y aplicar resultados a HubSpot.
    """
    # TODO Fase 5: implementar enriquecimiento completo
    pass
