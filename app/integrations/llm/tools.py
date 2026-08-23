"""
Definiciones de tools para function calling con Claude.
Tema #5: tool definitions — cada tool tiene su JSON schema completo.
"""

TOOLS = [
    {
        "name": "classify_customer_segment",
        "description": "Clasifica al cliente en un segmento de negocio basado en su email y datos disponibles.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Email del cliente"},
                "company_domain": {"type": "string", "description": "Dominio de la empresa extraído del email"},
                "segment": {
                    "type": "string",
                    "enum": ["enterprise", "smb", "startup", "individual"],
                    "description": "Segmento del cliente",
                },
                "industry": {"type": "string", "description": "Industria estimada de la empresa"},
                "company_size": {
                    "type": "string",
                    "enum": ["1-10", "11-50", "51-200", "201-1000", "1000+"],
                    "description": "Tamaño estimado de la empresa",
                },
            },
            "required": ["email", "segment"],
        },
    },
    {
        "name": "suggest_deal_priority",
        "description": "Sugiere la prioridad del deal basado en el monto del pago y el segmento del cliente.",
        "input_schema": {
            "type": "object",
            "properties": {
                "payment_amount_cents": {
                    "type": "integer",
                    "description": "Monto del pago en centavos",
                },
                "customer_segment": {
                    "type": "string",
                    "description": "Segmento del cliente (enterprise, smb, startup, individual)",
                },
                "priority": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Prioridad sugerida para el deal",
                },
                "reasoning": {"type": "string", "description": "Explicación de la prioridad asignada"},
            },
            "required": ["priority"],
        },
    },
]
