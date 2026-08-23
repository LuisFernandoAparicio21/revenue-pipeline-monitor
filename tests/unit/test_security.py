"""
Tests para la verificación HMAC-SHA256 de webhooks de Stripe.
Tema #2: validación de firma y anti-replay attack.
"""
import hashlib
import hmac
import time
import pytest

from app.core.security import verify_stripe_signature, WebhookSignatureError


def _make_sig_header(payload: bytes, secret: str, timestamp: int | None = None) -> str:
    ts = timestamp or int(time.time())
    signed = f"{ts}.{payload.decode()}"
    sig = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def test_valid_signature(monkeypatch):
    secret = "whsec_test_secret"
    monkeypatch.setattr("app.core.security.settings.STRIPE_WEBHOOK_SECRET", secret)
    monkeypatch.setattr("app.core.security.settings.STRIPE_WEBHOOK_TOLERANCE_SECONDS", 300)

    payload = b'{"id": "evt_test", "type": "invoice.payment_succeeded"}'
    sig_header = _make_sig_header(payload, secret)

    verify_stripe_signature(payload, sig_header)  # No debe lanzar excepción


def test_invalid_signature(monkeypatch):
    monkeypatch.setattr("app.core.security.settings.STRIPE_WEBHOOK_SECRET", "correct_secret")
    monkeypatch.setattr("app.core.security.settings.STRIPE_WEBHOOK_TOLERANCE_SECONDS", 300)

    payload = b'{"id": "evt_test"}'
    sig_header = _make_sig_header(payload, "wrong_secret")

    with pytest.raises(WebhookSignatureError, match="HMAC"):
        verify_stripe_signature(payload, sig_header)


def test_expired_timestamp(monkeypatch):
    secret = "whsec_test"
    monkeypatch.setattr("app.core.security.settings.STRIPE_WEBHOOK_SECRET", secret)
    monkeypatch.setattr("app.core.security.settings.STRIPE_WEBHOOK_TOLERANCE_SECONDS", 300)

    payload = b'{"id": "evt_old"}'
    old_timestamp = int(time.time()) - 400  # Más viejo que la ventana de 300s
    sig_header = _make_sig_header(payload, secret, timestamp=old_timestamp)

    with pytest.raises(WebhookSignatureError, match="Timestamp"):
        verify_stripe_signature(payload, sig_header)
