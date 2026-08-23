# Colección Postman — Revenue Pipeline Monitor

## Cómo importar

1. Abre Postman
2. Click en **Import**
3. Selecciona `RevenuePipeline.postman_collection.json`
4. Selecciona `Development.postman_environment.json`
5. Activa el environment **Development** en el selector superior derecho

## Variables de entorno requeridas

| Variable | Descripción |
|---|---|
| `base_url` | `http://localhost:8000` |
| `hubspot_client_id` | Tu HubSpot App Client ID |
| `hubspot_client_secret` | Tu HubSpot App Client Secret |
| `stripe_secret_key` | `sk_test_...` |
| `stripe_webhook_secret` | `whsec_...` |
| `access_token` | Se llena automáticamente con el pre-request script |

## Carpetas de la colección

- **Auth** — Flujo OAuth HubSpot completo (authorize → callback → refresh)
- **Webhooks** — Envío manual de eventos Stripe firmados
- **Health** — Estado de todas las integraciones
- **Admin** — Listar eventos, replay de fallidos

## Pre-request script OAuth

El script en la carpeta **Auth** refresca el token automáticamente antes de cada request si está próximo a expirar. No necesitas copiar tokens manualmente.

## Tema #8 del plan

Esta colección implementa el tema 8: Postman con environments, pre-request scripts para OAuth y JWT, y colecciones organizadas por dominio.
