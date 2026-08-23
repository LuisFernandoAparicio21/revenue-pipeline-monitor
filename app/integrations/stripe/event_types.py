from enum import Enum


class StripeEventType(str, Enum):
    CUSTOMER_CREATED = "customer.created"
    CHECKOUT_SESSION_COMPLETED = "checkout.session.completed"
    SUBSCRIPTION_CREATED = "customer.subscription.created"
    SUBSCRIPTION_UPDATED = "customer.subscription.updated"
    SUBSCRIPTION_DELETED = "customer.subscription.deleted"
    INVOICE_PAID = "invoice.payment_succeeded"
    INVOICE_FAILED = "invoice.payment_failed"
    PAYMENT_INTENT_SUCCEEDED = "payment_intent.succeeded"

    @classmethod
    def supported(cls) -> list[str]:
        return [e.value for e in cls]
