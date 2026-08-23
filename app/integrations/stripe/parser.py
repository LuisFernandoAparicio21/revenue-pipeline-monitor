import json
from app.integrations.stripe.schemas import (
    InternalStripeEvent, StripeCustomerData, StripePaymentData, StripeSubscriptionData
)
from app.integrations.stripe.event_types import StripeEventType


def parse_stripe_event(payload: bytes) -> InternalStripeEvent:
    """
    Transforma el payload raw de Stripe a un schema interno normalizado.
    Tema #10: requiere leer la doc de Stripe para cada tipo de evento.
    """
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise ValueError("Payload de Stripe no es JSON válido")

    event_id = data.get("id", "")
    event_type = data.get("type", "")
    obj = data.get("data", {}).get("object", {})

    if event_type not in StripeEventType.supported():
        raise ValueError(f"Tipo de evento no soportado: {event_type}")

    customer = None
    payment = None
    subscription = None

    if event_type == StripeEventType.CUSTOMER_CREATED:
        customer = StripeCustomerData(
            customer_id=obj.get("id", ""),
            email=obj.get("email"),
            name=obj.get("name"),
            phone=obj.get("phone"),
            metadata=obj.get("metadata", {}),
        )

    elif event_type in (StripeEventType.INVOICE_PAID, StripeEventType.INVOICE_FAILED):
        customer_id = obj.get("customer", "")
        payment = StripePaymentData(
            payment_id=obj.get("id", ""),
            customer_id=customer_id,
            amount=obj.get("amount_paid", 0) or obj.get("amount_due", 0),
            currency=obj.get("currency", "usd"),
            status="paid" if event_type == StripeEventType.INVOICE_PAID else "failed",
        )
        customer = StripeCustomerData(
            customer_id=customer_id,
            email=obj.get("customer_email"),
            name=obj.get("customer_name"),
        )

    elif event_type in (
        StripeEventType.SUBSCRIPTION_CREATED,
        StripeEventType.SUBSCRIPTION_UPDATED,
        StripeEventType.SUBSCRIPTION_DELETED,
    ):
        plan = obj.get("plan") or {}
        subscription = StripeSubscriptionData(
            subscription_id=obj.get("id", ""),
            customer_id=obj.get("customer", ""),
            plan_id=plan.get("id"),
            status=obj.get("status", "unknown"),
            amount=plan.get("amount", 0),
            currency=plan.get("currency", "usd"),
        )
        customer = StripeCustomerData(customer_id=obj.get("customer", ""))

    elif event_type == StripeEventType.CHECKOUT_SESSION_COMPLETED:
        customer = StripeCustomerData(
            customer_id=obj.get("customer", ""),
            email=obj.get("customer_email"),
        )
        payment = StripePaymentData(
            payment_id=obj.get("payment_intent", ""),
            customer_id=obj.get("customer", ""),
            amount=obj.get("amount_total", 0),
            currency=obj.get("currency", "usd"),
            status="paid",
        )

    return InternalStripeEvent(
        event_id=event_id,
        event_type=event_type,
        customer=customer,
        payment=payment,
        subscription=subscription,
        raw=data,
    )
