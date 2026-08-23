import hashlib
import hmac
import time

from app.core.config import settings


class WebhookSignatureError(Exception):
    pass


def verify_stripe_signature(payload_body: bytes, sig_header: str) -> None:
    """
    Verifica la firma HMAC-SHA256 de un webhook de Stripe.
    Lanza WebhookSignatureError si la firma es inválida o el timestamp es muy viejo.
    Tema #2 del plan: validación HMAC-SHA256 + anti-replay attack.
    """
    secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        parts = {k: v for part in sig_header.split(",") for k, v in [part.split("=", 1)]}
        timestamp = int(parts["t"])
        received_sig = parts["v1"]
    except (KeyError, ValueError):
        raise WebhookSignatureError("Header stripe-signature malformado")

    # Anti-replay: rechazar eventos con más de TOLERANCE segundos de antigüedad
    tolerance = settings.STRIPE_WEBHOOK_TOLERANCE_SECONDS
    if abs(time.time() - timestamp) > tolerance:
        raise WebhookSignatureError(
            f"Timestamp fuera de ventana permitida ({tolerance}s)"
        )

    signed_payload = f"{timestamp}.{payload_body.decode('utf-8')}"
    expected_sig = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    # compare_digest previene timing attacks
    if not hmac.compare_digest(expected_sig, received_sig):
        raise WebhookSignatureError("Firma HMAC-SHA256 inválida")
