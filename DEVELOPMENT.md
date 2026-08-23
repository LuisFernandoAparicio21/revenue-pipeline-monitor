# Guía de Desarrollo Local — Sin Docker

## Restricción de hardware documentada

Este proyecto corre **sin Docker** en desarrollo local.

| Recurso | Situación | Decisión |
|---------|-----------|----------|
| RAM total | ~8 GB | Sin Docker — evita WSL2 que consume 1-4GB extra |
| RAM libre | ~600 MB | Todo el stack local usa ~100MB |
| CPU | Buena | Celery worker sincrónico en dev (task_always_eager) |
| Base de datos | Azure ya pagada | PostgreSQL real en la nube, 0 RAM local |

## Stack por ambiente

| Componente | Desarrollo (local) | Producción |
|------------|-------------------|------------|
| Base de datos | **Azure PostgreSQL** (cloud, 0 RAM local) | Azure PostgreSQL (mismo servidor) |
| Redis | fakeredis (en memoria, ~10MB) | Redis real |
| Celery | `ALWAYS_EAGER=True` (sync) | Workers reales |
| Servidor | `uvicorn --reload` | Gunicorn + uvicorn workers |

## Por qué Azure PostgreSQL en dev y no SQLite

El servidor `market-db-server-luis` en Azure ya está pagado para otro proyecto.
Crear una nueva base de datos en él es **gratis** — el costo es por servidor, no por DB.
Esto nos da PostgreSQL real (no SQLite) con 0 MB de RAM local.

```
market-db-server-luis.postgres.database.azure.com
├── market_db          ← proyecto realtime-market-pipeline
└── revenue_pipeline_db ← este proyecto (creada 2026-08-23)
```
| Secrets | `.env` local | Variables de entorno del servidor |

## Setup inicial (una sola vez)

### 1. Python 3.11+
```bash
python --version   # debe ser 3.11 o superior
```

### 2. Entorno virtual
```bash
cd C:\Users\HP\Proyectos\revenue-pipeline-monitor
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell
```

### 3. Dependencias
```bash
pip install -r requirements-dev.txt
```

### 4. Variables de entorno
```bash
cp .env.example .env
# Editar .env con tus credenciales reales
```

### 5. Base de datos (SQLite — sin instalar nada)
```bash
python scripts/init_db.py
```

### 6. Arrancar el servidor
```bash
uvicorn app.main:app --reload --port 8000
```

### 7. Verificar
```
http://localhost:8000          → {"status": "online"}
http://localhost:8000/docs     → Swagger UI con todos los endpoints
```

## Variables de .env para desarrollo local

Las únicas variables obligatorias para empezar son:

```env
APP_ENV=development
APP_SECRET_KEY=cualquier_string_de_32_chars
DATABASE_URL=postgresql+asyncpg://adminuser:PASSWORD@market-db-server-luis.postgres.database.azure.com/revenue_pipeline_db?ssl=require
USE_FAKE_REDIS=true
CELERY_TASK_ALWAYS_EAGER=true

# Las demás se van agregando fase por fase:
# Fase 1: HUBSPOT_CLIENT_ID, HUBSPOT_CLIENT_SECRET
# Fase 2: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
# Fase 5: ANTHROPIC_API_KEY
```

## Uso de RAM estimado en dev

| Proceso | RAM aprox. |
|---------|-----------|
| uvicorn + FastAPI | ~80 MB |
| Azure PostgreSQL | **0 MB** (está en la nube) |
| fakeredis (en memoria) | ~10 MB |
| **Total local** | **~90 MB** |

Comparado con Docker completo (PostgreSQL + Redis + WSL2): ~1.5–2 GB. **20x menos RAM.**

## Workflow de ramas

```
main   ← código estable, una fase completa
  └── dev ← trabajo activo
        └── fase-X ← branch por fase (opcional)
```

Cuando terminas una fase:
```bash
git checkout dev
git add .
git commit -m "feat: fase X — descripción"
git push origin dev
# Cuando la fase está completa y verificada:
git checkout main
git merge dev
git push origin main
```
