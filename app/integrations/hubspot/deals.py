from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.hubspot.client import HubSpotClient
from app.integrations.hubspot.schemas import HubSpotDealProperties, HubSpotDeal
from app.core.config import settings


class HubSpotDeals:
    """
    CRUD de deals en HubSpot API v3.
    Tema #6: HubSpot REST API — deals pipeline.
    """

    def __init__(self, db: AsyncSession):
        self.client = HubSpotClient(db)
        self.base_path = "/crm/v3/objects/deals"

    async def create(self, properties: HubSpotDealProperties) -> HubSpotDeal:
        """Crea un deal en el pipeline configurado."""
        body = {"properties": properties.model_dump(exclude_none=True)}
        result = await self.client.post(self.base_path, body)
        return HubSpotDeal(**result)

    async def update_stage(self, deal_id: str, stage: str) -> HubSpotDeal:
        """Mueve un deal a otro stage del pipeline."""
        result = await self.client.patch(
            f"{self.base_path}/{deal_id}",
            {"properties": {"dealstage": stage}},
        )
        return HubSpotDeal(**result)

    async def associate_to_contact(self, deal_id: str, contact_id: str) -> None:
        """Asocia un deal con un contacto en HubSpot."""
        await self.client.put(
            f"/crm/v3/associations/deals/{deal_id}/contacts/{contact_id}/deal_to_contact",
            {},
        )
