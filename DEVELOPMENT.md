# Guía de Desarrollo Local — Sin Docker

## Restricción de hardware documentada

Este proyecto corre **sin Docker** en desarrollo local.

| Recurso | Situación | Decisión |
|---------|-----------|----------|
| RAM | Limitada | Sin Docker, sin contenedores en dev |
| CPU | Buena | Celery worker sincrónico en dev (task_always_eager) |
| Disco | Normal | SQLite en dev, PostgreSQL solo en staging/prod |

## Stack por ambiente

| Componente | Desarrollo (local) | Producción |
|------------|-------------------|------------|
| Base de datos | SQLite (archivo local) | PostgreSQL |
| Redis | fakeredis (en memoria) | Redis real |
| Celery | `ALWAYS_EAGER=True` (sync) | Workers reales |
| Servidor | `uvicorn --reload` | Gunicorn + uvicorn workers |
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
DATABASE_URL=sqlite+aiosqlite:///./dev.db
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
| SQLite | ~5 MB |
| fakeredis (en memoria) | ~10 MB |
| **Total** | **~100 MB** |

Comparado con Docker completo: ~1.5 GB. **15x menos RAM.**

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
