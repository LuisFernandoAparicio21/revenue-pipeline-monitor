from pydantic import BaseModel, EmailStr
from typing import Any


class StripeCustomerData(BaseModel):
    customer_id: str
    email: str | None = None
    name: str | None = None
    phone: str | None = None
    metadata: dict[str, Any] = {}


class StripePaymentData(BaseModel):
    payment_id: str
    customer_id: str | None = None
    amount: int = 0
    currency: str = "usd"
    status: str = "unknown"


class StripeSubscriptionData(BaseModel):
    subscription_id: str
    customer_id: str
    plan_id: str | None = None
    status: str = "unknown"
    amount: int = 0
    currency: str = "usd"


class InternalStripeEvent(BaseModel):
    event_id: str
    event_type: str
    customer: StripeCustomerData | None = None
    payment: StripePaymentData | None = None
    subscription: StripeSubscriptionData | None = None
    raw: dict[str, Any] = {}
