# Plan de Fases — Revenue Pipeline Monitor

## Cómo usar este documento

Cada fase tiene un objetivo práctico concreto.
No avances a la siguiente fase hasta que el "Verificación" de la actual funcione.
Todo el trabajo va en la branch `dev`. Al terminar una fase, merge a `main`.

---

## Fase 0 — Setup local sin Docker
**Objetivo:** El proyecto arranca en tu máquina, consume ~100MB de RAM, y el Swagger funciona.

### Qué hacer
1. Crear el entorno virtual e instalar `requirements-dev.txt`
2. Copiar `.env.example` a `.env` y configurar solo las variables de dev:
   ```env
   APP_ENV=development
   APP_SECRET_KEY=dev_secret_key_32_chars_minimum_
   DATABASE_URL=sqlite+aiosqlite:///./dev.db
   USE_FAKE_REDIS=true
   CELERY_TASK_ALWAYS_EAGER=true
   ENCRYPTION_KEY=   # generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   STRIPE_SECRET_KEY=placeholder
   STRIPE_WEBHOOK_SECRET=placeholder
   HUBSPOT_CLIENT_ID=placeholder
   HUBSPOT_CLIENT_SECRET=placeholder
   ANTHROPIC_API_KEY=placeholder
   ```
3. Inicializar la base de datos: `python scripts/init_db.py`
4. Arrancar el servidor: `uvicorn app.main:app --reload --port 8000`

### Verificación
- [ ] `http://localhost:8000` responde `{"status": "online"}`
- [ ] `http://localhost:8000/docs` muestra el Swagger con 4 secciones: Webhooks, OAuth, Health, Admin
- [ ] `http://localhost:8000/api/v1/health/integrations` responde (aunque diga unhealthy, debe responder)
- [ ] RAM usada: menos de 200MB

### Temas cubiertos
Ninguno de los 10 aún — esto es solo infraestructura.

---

## Fase 1 — OAuth 2.0 con HubSpot
**Objetivo:** Completar el flujo Authorization Code de HubSpot y obtener un access token real que se guarda en la DB cifrado y se refresca automáticamente.

**Tema cubierto: #1 — OAuth 2.0**

### Prerequisitos
- Cuenta de desarrollador en HubSpot (gratis): https://developers.hubspot.com
- Crear una App en el portal de developers
- Anotar `Client ID` y `Client Secret`
- Configurar Redirect URL: `http://localhost:8000/api/v1/oauth/hubspot/callback`
- ngrok para exponer localhost (gratis): https://ngrok.com

### Qué implementar / completar
- `app/integrations/hubspot/auth.py` ya existe — revisar y entender cada método
- Actualizar `.env` con `HUBSPOT_CLIENT_ID` y `HUBSPOT_CLIENT_SECRET` reales
- Verificar que `app/utils/crypto.py` funciona con tu `ENCRYPTION_KEY`

### Pasos prácticos
1. Iniciar ngrok: `ngrok http 8000`
2. Actualizar `HUBSPOT_REDIRECT_URI` en `.env` con la URL de ngrok
3. Abrir `http://localhost:8000/api/v1/oauth/hubspot/authorize` en el navegador
4. Completar el flujo de autorización en HubSpot
5. Verificar que el callback guardó el token en `dev.db`
6. Llamar `POST /api/v1/oauth/hubspot/refresh` y ver que retorna sin error

### Preguntas para entender mientras lo haces
- ¿Qué diferencia hay entre `client_id` y `client_secret`? ¿Cuál es público y cuál privado?
- ¿Por qué el `authorization_code` tiene vida corta (10 minutos)?
- ¿Por qué guardamos el token cifrado y no en texto plano?
- ¿Qué pasa si el `refresh_token` también expira?

### Verificación
- [ ] El flujo OAuth completo funciona en el navegador (redirect → login HubSpot → callback exitoso)
- [ ] En `dev.db`, tabla `oauth_tokens` tiene un registro con `integration = 'hubspot'`
- [ ] El `access_token` en la DB está cifrado (no es texto legible)
- [ ] `POST /api/v1/oauth/hubspot/refresh` retorna `{"status": "refreshed", "expires_at": "..."}`
- [ ] Si llamas refresh dos veces seguidas, la segunda usa el token cacheado (no llama a HubSpot)

---

## Fase 2 — HubSpot REST API: Contactos y Deals
**Objetivo:** Leer, crear y actualizar un contacto real en HubSpot desde código Python. Crear un deal asociado.

**Tema cubierto: #6 — HubSpot REST API**
**Tema secundario: #10 — Leer documentación de API nueva**

### Prerequisitos
- Fase 1 completada (token OAuth funcionando)
- Portal de HubSpot con datos de prueba (o sandbox)

### Qué implementar
- Crear `scripts/test_hubspot.py` — script de prueba manual
- Completar y probar `app/integrations/hubspot/contacts.py`
- Completar y probar `app/integrations/hubspot/deals.py`

### Pasos prácticos

**Paso 1 — Leer la documentación (Tema #10)**
Antes de escribir código, abrir:
- https://developers.hubspot.com/docs/api/crm/contacts
- https://developers.hubspot.com/docs/api/crm/deals

Responder por escrito (en un comentario o en papel):
1. ¿Cuál es el endpoint para crear un contacto?
2. ¿Cuáles son las propiedades obligatorias?
3. ¿Cómo se busca un contacto por email?
4. ¿Cómo se asocia un deal a un contacto?

**Paso 2 — Crear el script de prueba**
```python
# scripts/test_hubspot.py
# TODO: instanciar HubSpotContacts y probar:
# 1. search_by_email("test@empresa.com") → None (no existe)
# 2. create() con datos de prueba → retorna contacto con ID
# 3. search_by_email() de nuevo → retorna el contacto creado
# 4. update() cambiando el phone
# 5. Crear un deal y asociarlo al contacto
```

**Paso 3 — Postman (Tema #8 parcial)**
Crear en Postman:
- Request `GET /crm/v3/objects/contacts` contra `api.hubapi.com` con el Bearer token
- Request `POST /crm/v3/objects/contacts` con body JSON
- Guardar ambas como la carpeta `HubSpot API` en tu colección

### Preguntas para entender
- ¿Por qué HubSpot usa `properties` como wrapper en lugar de campos directos?
- ¿Qué pasa si intentas crear un contacto con un email que ya existe?
- ¿Cómo detectas si debes hacer POST (crear) o PATCH (actualizar)?

### Verificación
- [ ] `search_by_email("email_que_no_existe@test.com")` retorna `None`
- [ ] `create()` retorna un objeto con `id` numérico de HubSpot
- [ ] El contacto aparece en el portal de HubSpot
- [ ] `update()` cambia una propiedad y se ve reflejado en HubSpot
- [ ] El deal aparece en el pipeline de HubSpot asociado al contacto

---

## Fase 3 — Webhooks: Receptor + HMAC + Async
**Objetivo:** Recibir un webhook real de Stripe, validar su firma HMAC-SHA256, y procesarlo de forma asíncrona sin bloquear la respuesta HTTP.

**Tema cubierto: #2 — Webhooks**

### Prerequisitos
- Cuenta de Stripe (gratis): https://dashboard.stripe.com
- Stripe CLI instalado: https://stripe.com/docs/stripe-cli
- ngrok corriendo

### Qué implementar
- El endpoint `POST /api/v1/webhooks/stripe` ya existe — hay que probarlo
- Entender cada línea de `app/core/security.py`
- Entender `app/services/idempotency.py` (la verificación Redis)

### Pasos prácticos

**Paso 1 — Entender el código de validación HMAC**
Abrir `app/core/security.py` y responder:
1. ¿Qué es `hmac.compare_digest` y por qué no se usa `==`?
2. ¿Qué es un timing attack?
3. ¿Por qué verificamos el timestamp además de la firma?

**Paso 2 — Probar con Stripe CLI**
```bash
# Terminal 1: servidor corriendo
uvicorn app.main:app --reload --port 8000

# Terminal 2: Stripe CLI reenvía webhooks a tu local
stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe

# Terminal 3: disparar un evento de prueba
stripe trigger invoice.payment_succeeded
```

**Paso 3 — Verificar la validación**
Intentar enviar un webhook con firma incorrecta:
```bash
curl -X POST http://localhost:8000/api/v1/webhooks/stripe \
  -H "Content-Type: application/json" \
  -H "stripe-signature: t=1234,v1=firma_falsa" \
  -d '{"id":"evt_test","type":"invoice.payment_succeeded"}'
```
Debe responder `401 Unauthorized`.

**Paso 4 — Verificar respuesta async**
El endpoint debe responder HTTP 200 en menos de 500ms aunque el procesamiento tarde.
Revisar los logs: el 200 debe aparecer antes que cualquier log de procesamiento.

### Preguntas para entender
- ¿Por qué Stripe firma con HMAC-SHA256 y no con una API key en el header?
- ¿Qué es un replay attack y cómo lo previene la ventana de 5 minutos?
- ¿Por qué respondemos 200 inmediatamente en vez de esperar a procesar?

### Verificación
- [ ] `stripe trigger invoice.payment_succeeded` → el servidor recibe y responde 200
- [ ] El evento aparece en tabla `webhook_events` de `dev.db`
- [ ] Firma inválida → responde 401 (nunca 200)
- [ ] Timestamp viejo → responde 401 con mensaje "Timestamp fuera de ventana"
- [ ] La respuesta 200 llega en menos de 500ms (medir con Postman o logs)

---

## Fase 4 — Idempotencia: Que ningún evento se procese dos veces
**Objetivo:** Enviar el mismo evento 5 veces consecutivas y confirmar que solo se procesa una vez.

**Tema cubierto: #4 — Idempotencia**

### Por qué importa esto
Stripe puede enviar el mismo webhook múltiples veces si no recibe respuesta rápido.
Si cada recepción crea un contacto nuevo en HubSpot, el CRM se llena de duplicados.
La idempotencia garantiza: sin importar cuántas veces llegue el mismo evento, el efecto es el mismo que si hubiera llegado una sola vez.

### Qué implementar
- `app/services/idempotency.py` ya existe — entender las dos capas
- Adaptar para usar `fakeredis` en dev (está configurado si `USE_FAKE_REDIS=true`)

### Pasos prácticos

**Paso 1 — Entender las dos capas**
```
Capa 1: Redis (SETNX)
  → Rápido: responde en microsegundos
  → Problema: si Redis se reinicia, pierde la memoria

Capa 2: PostgreSQL / SQLite (tabla webhook_events)
  → Lento pero persistente
  → Backup si Redis falla
```

**Paso 2 — Crear el test de idempotencia**
```python
# tests/unit/test_idempotency.py
# Enviar el mismo event_id 5 veces
# Verificar que solo hay 1 registro en webhook_events
# Verificar que las 5 respuestas son 200 (no 4xx)
# Verificar que la segunda respuesta incluye "status": "duplicate"
```

**Paso 3 — Probar manualmente con curl**
```bash
# Enviar el mismo evento dos veces seguidas con el mismo event_id
# La primera vez: {"received": true, "status": "queued"}
# La segunda vez: {"received": true, "status": "duplicate"}
```

**Paso 4 — Simular fallo de Redis**
Con `fakeredis`, limpiar el store y enviar el mismo evento.
La segunda capa (DB) debe atraparlo igual.

### Preguntas para entender
- ¿Qué es SETNX y cómo garantiza atomicidad?
- ¿Por qué el TTL de idempotencia es 24 horas y no infinito?
- ¿Qué pasa si dos workers de Celery reciben el mismo evento simultáneamente?
- ¿Cuál es la diferencia entre idempotencia "a nivel HTTP" y "a nivel de negocio"?

### Verificación
- [ ] Mismo evento enviado 5 veces → tabla `webhook_events` tiene exactamente 1 registro
- [ ] La primera respuesta: `{"status": "queued"}`
- [ ] La segunda en adelante: `{"status": "duplicate"}`
- [ ] Los logs muestran "duplicado detectado" para los envíos 2-5
- [ ] Test unitario en `tests/unit/test_idempotency.py` pasa

---

## Fase 5 — Retry + Exponential Backoff + Rate Limiting
**Objetivo:** El sistema maneja automáticamente errores 429 y 5xx de HubSpot sin intervención manual, usando backoff exponencial y sin destruir el rate limit.

**Temas cubiertos: #3 — Retry/Backoff y #7 — Rate Limiting**

### Prerequisitos
- Fases 1 y 2 completadas (cliente HubSpot funcionando)

### Qué implementar
- `app/utils/backoff.py` ya existe — entender los decoradores de tenacity
- `app/integrations/hubspot/rate_limiter.py` — entender el token bucket
- Crear script para simular errores 429

### Pasos prácticos

**Paso 1 — Entender tenacity**
Abrir `app/utils/backoff.py`. Con papel y lápiz, dibujar la secuencia de tiempos de espera para `retry_on_server_error`:
- Intento 1: falla → espera X segundos
- Intento 2: falla → espera Y segundos
- Intento 3: falla → espera Z segundos
- ...

**Paso 2 — Simular un 429 de HubSpot**
```python
# scripts/simulate_rate_limit.py
# Hacer 20 requests a HubSpot en 1 segundo
# Observar qué pasa: ¿recibimos 429?
# ¿El rate_limiter.py lo detecta?
# ¿Qué header viene en la respuesta 429?
```

**Paso 3 — Leer el header Retry-After**
Cuando HubSpot responde 429, revisa los headers de la respuesta.
Busca en la documentación de HubSpot qué headers envía en un 429.
Verificar que `backoff_on_429()` los está leyendo correctamente.

**Paso 4 — Token bucket**
Abrir `app/integrations/hubspot/rate_limiter.py`.
Responder: ¿por qué un token bucket es mejor que un simple `time.sleep(0.1)` entre requests?

**Paso 5 — Postman (Tema #8 parcial)**
En Postman, crear un test que envíe 15 requests en 2 segundos y mida cuántos responden 200 vs 429.

### Preguntas para entender
- ¿Qué es "jitter" en exponential backoff y por qué es importante cuando hay muchos clientes?
- ¿Cuál es la diferencia entre retry a nivel de HTTP y retry a nivel de Celery task?
- ¿Qué pasa si nunca paras de reintentar? ¿Cómo defines el límite?
- ¿Cuándo NO debes reintentar? (Pista: piensa en los códigos 4xx)

### Verificación
- [ ] 10 requests rápidos a HubSpot → el rate_limiter espacía las llamadas automáticamente
- [ ] Un 429 simulado → el sistema espera y reintenta (ver en logs)
- [ ] Un error 500 simulado → 3 reintentos con backoff exponencial, luego falla definitivamente
- [ ] Un error 400 (Bad Request) → NO reintenta (es un error del cliente, no del servidor)
- [ ] Test unitario para el token bucket pasa

---

## Fase 6 — Function Calling con Claude
**Objetivo:** Claude analiza un email de contacto nuevo, llama tools para clasificarlo, y retorna datos estructurados que se guardan en HubSpot.

**Tema cubierto: #5 — Function Calling con LLMs**

### Prerequisitos
- API key de Anthropic: https://console.anthropic.com
- Fases 1 y 2 completadas (HubSpot funcionando)

### Qué implementar
- `app/integrations/llm/tools.py` — las definiciones ya existen, entenderlas
- `app/integrations/llm/client.py` — el ciclo de tool_use ya existe
- `app/integrations/llm/enrichment.py` — el orquestador ya existe
- Crear `scripts/test_enrichment.py` para probar manualmente

### Pasos prácticos

**Paso 1 — Entender el ciclo de tool_use**
Dibujar el flujo completo con papel:
```
Tu código → Claude (con tools definidas)
Claude → responde con tool_use block (quiere llamar una tool)
Tu código → ejecuta la tool (función Python real)
Tu código → envía tool_result de vuelta a Claude
Claude → responde con texto final usando el resultado
```
¿Cuántos round-trips hay hacia la API de Anthropic?

**Paso 2 — Probar las tools manualmente**
```python
# scripts/test_enrichment.py
from app.integrations.llm.enrichment import ContactEnrichmentAgent

agent = ContactEnrichmentAgent()
result = agent.enrich("ceo@microsoft.com", payment_amount_cents=99900)
print(result)
# Esperado: {"segment": "enterprise", "industry": "technology", "deal_priority": "high"}

result2 = agent.enrich("usuario@gmail.com", payment_amount_cents=999)
print(result2)
# Esperado: {"segment": "individual", "deal_priority": "low"}
```

**Paso 3 — Inspeccionar el tool_use en los logs**
Activar logging detallado y ver exactamente qué manda Claude en el `tool_use` block.
¿Qué campos vienen? ¿Cómo se llama la tool? ¿Qué `input` pasa?

**Paso 4 — Agregar una tool nueva**
Crear una tool `detect_language` que detecte el idioma del dominio del email (ej: `.mx` → español, `.de` → alemán).
Agregar la definición en `tools.py` y la lógica de ejecución.

**Paso 5 — Conectar con HubSpot**
Después del enriquecimiento, llamar a `contacts.update()` para guardar `segment` y `deal_priority` como propiedades custom en HubSpot.

### Preguntas para entender
- ¿Cuál es la diferencia entre function calling y prompt engineering simple?
- ¿Por qué Claude no ejecuta las tools directamente? ¿Por qué las ejecuta tu código?
- ¿Qué pasa si Claude llama una tool que no existe en tu definición?
- ¿Cómo manejas el caso donde Claude no llama ninguna tool?

### Verificación
- [ ] `agent.enrich("director@bigcorp.com", 500000)` → segment enterprise, priority high
- [ ] `agent.enrich("personal@hotmail.com", 999)` → segment individual, priority low
- [ ] Los logs muestran el tool_use block que Claude generó
- [ ] La tool nueva `detect_language` funciona y Claude la llama cuando corresponde
- [ ] El contacto en HubSpot tiene las propiedades de enriquecimiento guardadas

---

## Fase 7 — Pipeline Completo: Stripe → HubSpot
**Objetivo:** Un pago real en Stripe resulta automáticamente en un contacto y un deal en HubSpot, sin intervención manual.

**Integra todos los temas anteriores: #1, #2, #3, #4, #5, #6, #7**

### Qué implementar
- `app/services/sync_orchestrator.py` — el cerebro del sistema (TODO en Fase 4 del código)
- Conectar `app/tasks/hubspot_tasks.py` con el orquestador
- `app/tasks/enrichment_tasks.py` — encolar el enriquecimiento LLM

### Pasos prácticos

**Paso 1 — Implementar sync_orchestrator.py**
```python
# app/services/sync_orchestrator.py
class SyncOrchestrator:
    async def run(self, event: InternalStripeEvent, db: AsyncSession):
        # 1. Marcar evento como "processing"
        # 2. Extraer datos del cliente del evento
        # 3. Buscar contacto en HubSpot por email
        # 4. Si no existe → crear contacto
        # 5. Si existe → actualizar propiedades
        # 6. Crear o actualizar deal
        # 7. Si contacto es nuevo → encolar enriquecimiento LLM
        # 8. Registrar sync_record
        # 9. Marcar evento como "completed"
```

**Paso 2 — Probar el flujo completo**
```bash
# 1. Asegurarse de que uvicorn está corriendo
# 2. stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe
# 3. stripe trigger invoice.payment_succeeded
# 4. Verificar en HubSpot que apareció el contacto
# 5. Verificar que el deal está en el pipeline
# 6. Verificar que el contacto tiene propiedades de enriquecimiento LLM
```

**Paso 3 — Simular un fallo a mitad del pipeline**
Desconectar temporalmente (comentar el código) la llamada a HubSpot deals.
Enviar un evento. ¿El contacto se crea pero el deal no?
¿El evento queda en estado "failed" o "partial"?
¿Se puede hacer replay desde el admin endpoint?

### Verificación
- [ ] `stripe trigger invoice.payment_succeeded` → contacto aparece en HubSpot en menos de 10 segundos
- [ ] El deal aparece en el pipeline de HubSpot asociado al contacto
- [ ] Segundo trigger con mismo email → contacto se ACTUALIZA, no se duplica
- [ ] El contacto tiene las propiedades de enriquecimiento LLM
- [ ] `GET /api/v1/admin/events` muestra el evento con status "completed"
- [ ] Fallo simulado → evento en "failed" → replay desde admin → se completa

---

## Fase 8 — Postman: Colección Profesional
**Objetivo:** Cualquier desarrollador puede importar la colección, llenar el environment, y probar todo el sistema sin leer el código.

**Tema cubierto: #8 — Postman**

### Qué crear en Postman

**Carpeta 1: Auth**
- `GET /api/v1/oauth/hubspot/authorize` — inicia el flujo OAuth
- `POST /api/v1/oauth/hubspot/refresh` — refresca el token
- Pre-request script que verifica si el token está próximo a expirar y lo refresca antes de cada request

**Carpeta 2: Webhooks (Pruebas manuales)**
- `POST /api/v1/webhooks/stripe` con payload de invoice.payment_succeeded firmado
- Script de pre-request que genera la firma HMAC-SHA256 automáticamente
- Test que verifica que la respuesta sea `{"received": true}`

**Carpeta 3: Health**
- `GET /api/v1/health/integrations` — estado de todas las integraciones
- `GET /api/v1/health/integrations/hubspot` — solo HubSpot
- Test que falla si alguna integración está unhealthy

**Carpeta 4: Admin**
- `GET /api/v1/admin/events?status=failed` — eventos fallidos
- `POST /api/v1/admin/events/{event_id}/replay` — replay de un evento

**Environment: Development**
```
base_url = http://localhost:8000
hubspot_client_id = {{tu_client_id}}
stripe_webhook_secret = {{tu_secret}}
access_token = (se llena automáticamente con el pre-request script)
```

### Pre-request script OAuth (el más importante)
```javascript
// Se ejecuta antes de cada request autenticado
// Si el token está próximo a expirar, llama al endpoint de refresh
// y guarda el nuevo token en la variable de entorno
pm.sendRequest({
    url: pm.environment.get("base_url") + "/api/v1/oauth/hubspot/refresh",
    method: "POST"
}, function(err, res) {
    if (!err) {
        // guardar token para el request actual
    }
});
```

### Verificación
- [ ] Collection runner ejecuta todos los requests sin errores manuales
- [ ] El pre-request script de OAuth refresca el token automáticamente
- [ ] El webhook firmado desde Postman es aceptado por el servidor (no 401)
- [ ] Colección exportada y el README de postman/ explica cómo importarla
- [ ] Otra persona puede importar la colección y usarla sin preguntar nada

---

## Fase 9 — Observabilidad y Troubleshooting Sistemático
**Objetivo:** Cuando algo falla, el sistema lo detecta, lo registra, y proporciona herramientas para diagnosticar y recuperarse.

**Temas cubiertos: #9 — Troubleshooting sistemático**

### Qué implementar / completar
- `app/services/health_checker.py` — ya existe, completar las verificaciones
- `app/api/v1/health.py` — conectar con health_checker
- `app/api/v1/admin.py` — completar el endpoint de replay
- `scripts/replay_events.py` — para recuperación masiva de eventos fallidos
- `docs/troubleshooting.md` — guía de debug paso a paso

### La metodología de troubleshooting (documentar esto)

```
Cuando una integración falla, el flujo de debug es siempre:

PASO 1 — AUTH
  ¿Tenemos un token válido?
  → GET /api/v1/health/integrations
  → Si HubSpot dice unhealthy: GET /api/v1/oauth/hubspot/refresh

PASO 2 — REQUEST
  ¿Estamos construyendo el request correctamente?
  → Revisar logs del evento fallido en GET /api/v1/admin/events
  → Reproducir el request en Postman con los mismos datos

PASO 3 — RESPONSE
  ¿Qué respondió HubSpot exactamente?
  → Buscar en logs el status code y el body completo
  → Si es 400: problema en los datos que mandamos
  → Si es 429: rate limiting (ver token bucket)
  → Si es 5xx: problema en HubSpot (reintento)

PASO 4 — DATOS
  ¿Los datos llegaron correctamente al destino?
  → Buscar el contacto en HubSpot portal directamente
  → Comparar con lo que dice sync_records en la DB
  → Si hay discrepancia: replay del evento
```

### Crear `docs/troubleshooting.md`
Documentar el flujo anterior con ejemplos reales de errores que te hayan ocurrido en las fases anteriores.

### Verificación
- [ ] `GET /api/v1/health/integrations` retorna estado real de HubSpot, Stripe, Redis y DB
- [ ] Cuando HubSpot está caído: health endpoint lo refleja en menos de 5 segundos
- [ ] Un evento fallido puede hacerse replay desde el admin endpoint
- [ ] `scripts/replay_events.py` re-encola todos los eventos en estado "failed"
- [ ] `docs/troubleshooting.md` tiene el flujo de debug documentado con ejemplos reales

---

## Fase 10 — API Nueva: Integrar Slack en 2 horas
**Objetivo:** Aplicar todo lo aprendido a una API que no conoces. Sin tutoriales — solo la documentación oficial.

**Tema cubierto: #10 — Leer documentación y definir estrategia**

### El reto
Conectar Slack para enviar una notificación cuando un deal de alto valor se crea en HubSpot.

**Solo puedes usar:**
- La documentación oficial de Slack: https://api.slack.com
- Lo que ya sabes de las fases anteriores

**No puedes usar:**
- Tutoriales de Slack
- Librerías wrapper de Slack
- Código que no escribiste tú

### Proceso obligatorio (documentar cada paso)

**Paso 1 — Exploración (30 min)**
Leer la documentación de Slack API y responder:
1. ¿Qué tipo de autenticación usa Slack? ¿OAuth? ¿API Key? ¿Bot token?
2. ¿Cuál es el endpoint para enviar un mensaje a un canal?
3. ¿Qué permisos (scopes) necesitas?
4. ¿Tiene rate limiting? ¿Cuántos requests por segundo?
5. ¿Tiene webhooks? ¿Cómo se valida la firma?

**Paso 2 — Estrategia (15 min)**
Antes de escribir código, definir por escrito:
- ¿Qué tipo de autenticación implementaré?
- ¿Qué endpoint usaré?
- ¿Cómo manejaré los errores?
- ¿Cómo adaptaré el retry logic que ya tenemos?

**Paso 3 — Implementación (75 min)**
```
app/integrations/slack/
├── __init__.py
├── client.py       # HTTP client reutilizando utils/backoff.py
└── notifications.py # Enviar mensaje cuando deal > $500 USD
```

**Paso 4 — Integración**
En `sync_orchestrator.py`, después de crear el deal:
```python
if deal_amount > 50000:  # centavos = $500 USD
    slack.send_high_value_deal_alert(contact_email, deal_amount)
```

### Verificación
- [ ] `stripe trigger invoice.payment_succeeded` con amount 99900 → mensaje en Slack
- [ ] El client de Slack reutiliza `utils/backoff.py` (sin copiar código)
- [ ] La estrategia está documentada en `app/integrations/slack/README.md`
- [ ] El código no usa ninguna librería de Slack — solo httpx + tu client base

---

## Resumen de todas las fases

| Fase | Nombre | Temas | Duración estimada |
|------|--------|-------|-------------------|
| 0 | Setup local sin Docker | — | 1 hora |
| 1 | OAuth 2.0 con HubSpot | #1 | 2-3 horas |
| 2 | HubSpot REST API | #6, #10 | 3-4 horas |
| 3 | Webhooks Stripe | #2 | 2-3 horas |
| 4 | Idempotencia | #4 | 2 horas |
| 5 | Retry + Rate Limiting | #3, #7 | 3 horas |
| 6 | Function Calling LLM | #5 | 3-4 horas |
| 7 | Pipeline Completo | todos | 4-5 horas |
| 8 | Postman Profesional | #8 | 2-3 horas |
| 9 | Observabilidad | #9 | 2-3 horas |
| 10 | API Nueva: Slack | #10 | 2 horas |

**Total estimado: 25-35 horas de práctica real.**

## Regla de oro

> Nunca copies código sin entenderlo.
> Si no puedes explicar por qué está esa línea, no la pongas.
> El objetivo no es que el proyecto funcione — es que TÚ entiendas por qué funciona.
