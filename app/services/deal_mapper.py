from datetime import datetime, timezone

from app.integrations.stripe.schemas import StripePaymentData, StripeSubscriptionData
from app.integrations.hubspot.schemas import HubSpotDealProperties
from app.core.config import settings


def stripe_payment_to_hubspot_deal(
    payment: StripePaymentData,
    contact_email: str,
) -> HubSpotDealProperties:
    """
    Mapeo Stripe Payment → HubSpot Deal.
    Tema #10: mapeo entre APIs con documentaciones distintas.
    """
    amount_usd = payment.amount / 100  # Stripe usa centavos

    return HubSpotDealProperties(
        dealname=f"Payment {payment.payment_id[:8]} — {contact_email}",
        amount=str(amount_usd),
        dealstage=settings.HUBSPOT_DEAL_STAGE_PAID if payment.status == "paid"
                  else settings.HUBSPOT_DEAL_STAGE_NEW,
        pipeline=settings.HUBSPOT_DEAL_PIPELINE_ID,
        closedate=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    )


def stripe_subscription_to_hubspot_deal(
    subscription: StripeSubscriptionData,
    contact_email: str,
) -> HubSpotDealProperties:
    """Mapeo Stripe Subscription → HubSpot Deal."""
    amount_usd = subscription.amount / 100

    stage_map = {
        "active": settings.HUBSPOT_DEAL_STAGE_PAID,
        "canceled": settings.HUBSPOT_DEAL_STAGE_CHURNED,
        "trialing": settings.HUBSPOT_DEAL_STAGE_NEW,
        "past_due": settings.HUBSPOT_DEAL_STAGE_NEW,
    }
    stage = stage_map.get(subscription.status, settings.HUBSPOT_DEAL_STAGE_NEW)

    return HubSpotDealProperties(
        dealname=f"Subscription {subscription.subscription_id[:8]} — {contact_email}",
        amount=str(amount_usd),
        dealstage=stage,
        pipeline=settings.HUBSPOT_DEAL_PIPELINE_ID,
    )
