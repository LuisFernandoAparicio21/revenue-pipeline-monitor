import anthropic
from app.core.config import settings


class LLMClient:
    """
    Wrapper sobre el SDK de Anthropic con soporte para tool use multi-turno.
    Tema #5: ciclo completo de function calling con Claude.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.LLM_MODEL
        self.max_tokens = settings.LLM_MAX_TOKENS

    def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        system: str | None = None,
    ) -> dict:
        """
        Ejecuta el ciclo completo de tool use:
        1. Claude responde con tool_use blocks
        2. Ejecutamos las tools (funciones Python reales)
        3. Enviamos tool_result de vuelta a Claude
        4. Claude genera respuesta final

        Retorna dict con los resultados de todas las tool calls.
        """
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "tools": tools,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)
        tool_results = {}

        # Procesar tool_use blocks en la respuesta
        for block in response.content:
            if block.type == "tool_use":
                tool_results[block.name] = block.input

        return tool_results
