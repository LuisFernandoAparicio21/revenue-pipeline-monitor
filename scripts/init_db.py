"""
Script de inicialización de la base de datos para desarrollo local.
Crea todas las tablas en SQLite sin necesidad de correr Alembic.
Uso: python scripts/init_db.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base
import app.models.webhook_event      # noqa
import app.models.sync_record        # noqa
import app.models.oauth_token        # noqa
import app.models.contact_enrichment # noqa


async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Base de datos inicializada correctamente.")
    print("Archivo creado: dev.db")


if __name__ == "__main__":
    asyncio.run(init())
