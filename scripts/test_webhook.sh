#!/bin/bash
# Script para enviar un webhook de prueba firmado manualmente.
# Requiere: STRIPE_WEBHOOK_SECRET en el entorno.
# Uso: ./scripts/test_webhook.sh

PAYLOAD='{"id":"evt_test_manual","type":"invoice.payment_succeeded","data":{"object":{"id":"in_test","customer":"cus_test","customer_email":"luis@test.com","customer_name":"Luis Fernando","amount_paid":9900,"currency":"usd","status":"paid"}}}'
TIMESTAMP=$(date +%s)
SECRET="${STRIPE_WEBHOOK_SECRET:-whsec_test}"
SIGNED="${TIMESTAMP}.${PAYLOAD}"
SIG=$(echo -n "$SIGNED" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.* //')

curl -X POST http://localhost:8000/api/v1/webhooks/stripe \
  -H "Content-Type: application/json" \
  -H "stripe-signature: t=${TIMESTAMP},v1=${SIG}" \
  -d "$PAYLOAD"
