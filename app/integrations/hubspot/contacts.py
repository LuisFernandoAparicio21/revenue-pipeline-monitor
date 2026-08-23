from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.hubspot.client import HubSpotClient
from app.integrations.hubspot.schemas import HubSpotContactProperties, HubSpotContact


class HubSpotContacts:
    """
    CRUD de contactos en HubSpot API v3.
    Tema #6: HubSpot REST API — contactos.
    """

    def __init__(self, db: AsyncSession):
        self.client = HubSpotClient(db)
        self.base_path = "/crm/v3/objects/contacts"

    async def search_by_email(self, email: str) -> HubSpotContact | None:
        """Busca un contacto por email. Retorna None si no existe."""
        body = {
            "filterGroups": [
                {
                    "filters": [
                        {"propertyName": "email", "operator": "EQ", "value": email}
                    ]
                }
            ],
            "properties": ["email", "firstname", "lastname", "phone", "company"],
            "limit": 1,
        }
        result = await self.client.post(f"{self.base_path}/search", body)
        results = result.get("results", [])
        if not results:
            return None
        return HubSpotContact(**results[0])

    async def create(self, properties: HubSpotContactProperties) -> HubSpotContact:
        """Crea un nuevo contacto en HubSpot."""
        body = {"properties": properties.model_dump(exclude_none=True)}
        result = await self.client.post(self.base_path, body)
        return HubSpotContact(**result)

    async def update(self, contact_id: str, properties: dict) -> HubSpotContact:
        """Actualiza propiedades de un contacto existente."""
        body = {"properties": properties}
        result = await self.client.patch(f"{self.base_path}/{contact_id}", body)
        return HubSpotContact(**result)

    async def get_by_id(self, contact_id: str) -> HubSpotContact:
        result = await self.client.get(f"{self.base_path}/{contact_id}")
        return HubSpotContact(**result)
