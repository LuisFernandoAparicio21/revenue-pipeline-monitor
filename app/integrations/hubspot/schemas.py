from pydantic import BaseModel
from typing import Any


class HubSpotContactProperties(BaseModel):
    email: str
    firstname: str | None = None
    lastname: str | None = None
    phone: str | None = None
    company: str | None = None
    lifecyclestage: str = "lead"
    hs_lead_status: str | None = None
    # Propiedades custom (se agregan en Fase 5 con LLM)
    customer_segment: str | None = None
    deal_priority: str | None = None


class HubSpotContact(BaseModel):
    id: str
    properties: dict[str, Any]
    created_at: str | None = None
    updated_at: str | None = None


class HubSpotDealProperties(BaseModel):
    dealname: str
    amount: str | None = None
    dealstage: str
    pipeline: str
    closedate: str | None = None
    hubspot_owner_id: str | None = None


class HubSpotDeal(BaseModel):
    id: str
    properties: dict[str, Any]
