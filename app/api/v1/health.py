from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.health_checker import HealthChecker

router = APIRouter()


@router.get("/integrations")
async def check_integrations(db: AsyncSession = Depends(get_db)):
    """
    Verifica el estado en tiempo real de todas las integraciones.
    Tema #9: observabilidad y troubleshooting sistemático.
    """
    checker = HealthChecker(db)
    return await checker.check_all()


@router.get("/integrations/{integration}")
async def check_single_integration(
    integration: str,
    db: AsyncSession = Depends(get_db),
):
    checker = HealthChecker(db)
    return await checker.check_one(integration)
