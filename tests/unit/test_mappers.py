"""
Tests para los mappers Stripe → HubSpot.
Funciones puras: sin red, sin DB.
"""
from app.integrations.stripe.schemas import StripeCustomerData, StripePaymentData
from app.services.contact_mapper import (
    stripe_customer_to_hubspot_contact,
    stripe_payment_to_contact_update,
)


def test_customer_to_contact_full_name():
    customer = StripeCustomerData(
        customer_id="cus_test",
        email="luis@empresa.com",
        name="Luis Fernando",
        phone="+52 55 1234 5678",
    )
    contact = stripe_customer_to_hubspot_contact(customer)

    assert contact.email == "luis@empresa.com"
    assert contact.firstname == "Luis"
    assert contact.lastname == "Fernando"
    assert contact.phone == "+52 55 1234 5678"
    assert contact.lifecyclestage == "lead"


def test_customer_to_contact_single_name():
    customer = StripeCustomerData(customer_id="cus_test", email="test@co.com", name="Luis")
    contact = stripe_customer_to_hubspot_contact(customer)
    assert contact.firstname == "Luis"
    assert contact.lastname is None


def test_payment_update_on_success():
    payment = StripePaymentData(
        payment_id="pi_test", customer_id="cus_test", amount=5000, status="paid"
    )
    update = stripe_payment_to_contact_update(payment)
    assert update["lifecyclestage"] == "customer"
    assert update["hs_lead_status"] == "CUSTOMER"
