from app.integrations.llm.client import LLMClient
from app.integrations.llm.tools import TOOLS
from app.core.config import settings


class ContactEnrichmentAgent:
    """
    Orquestador del enriquecimiento de contactos con LLM.
    Tema #5: function calling completo — Claude analiza el contacto y llama tools.
    """

    def __init__(self):
        self.llm = LLMClient()

    def enrich(self, email: str, payment_amount_cents: int = 0) -> dict:
        """
        Enriquece un contacto nuevo usando Claude con function calling.
        Retorna dict con segment, industry, company_size, deal_priority.
        """
        if not settings.LLM_ENRICHMENT_ENABLED:
            return {}

        domain = email.split("@")[-1] if "@" in email else ""

        system_prompt = (
            "Eres un especialista en clasificación de clientes B2B y B2C. "
            "Analiza los datos del cliente y usa las herramientas disponibles "
            "para clasificarlo y sugerir la prioridad del deal. "
            "Sé conciso y basate en el dominio del email y el monto del pago."
        )

        messages = [
            {
                "role": "user",
                "content": (
                    f"Analiza este nuevo cliente:\n"
                    f"- Email: {email}\n"
                    f"- Dominio de empresa: {domain}\n"
                    f"- Monto del pago: ${payment_amount_cents / 100:.2f} USD\n\n"
                    f"Clasifícalo en un segmento y sugiere la prioridad del deal."
                ),
            }
        ]

        tool_results = self.llm.complete_with_tools(
            messages=messages,
            tools=TOOLS,
            system=system_prompt,
        )

        enrichment = {}

        if "classify_customer_segment" in tool_results:
            data = tool_results["classify_customer_segment"]
            enrichment["segment"] = data.get("segment")
            enrichment["industry"] = data.get("industry")
            enrichment["company_size"] = data.get("company_size")

        if "suggest_deal_priority" in tool_results:
            data = tool_results["suggest_deal_priority"]
            enrichment["deal_priority"] = data.get("priority")

        return enrichment
