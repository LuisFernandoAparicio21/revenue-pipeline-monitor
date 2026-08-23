from app.integrations.stripe.schemas import StripeCustomerData, StripePaymentData
from app.integrations.hubspot.schemas import HubSpotContactProperties


def stripe_customer_to_hubspot_contact(customer: StripeCustomerData) -> HubSpotContactProperties:
    """
    Mapeo puro Stripe Customer → HubSpot Contact.
    Tema #10: requiere leer ambas documentaciones para mapear los campos.
    Función pura: sin efectos secundarios, completamente testeable.
    """
    name_parts = (customer.name or "").strip().split(" ", 1)
    firstname = name_parts[0] if name_parts else None
    lastname = name_parts[1] if len(name_parts) > 1 else None

    return HubSpotContactProperties(
        email=customer.email or "",
        firstname=firstname,
        lastname=lastname,
        phone=customer.phone,
        lifecyclestage="lead",
    )


def stripe_payment_to_contact_update(payment: StripePaymentData) -> dict:
    """
    Actualización de contacto basada en un pago exitoso.
    Mueve el lifecyclestage a 'customer' cuando paga.
    """
    update = {"lifecyclestage": "customer"}
    if payment.status == "paid":
        update["hs_lead_status"] = "CUSTOMER"
    return update


def stripe_payment_to_contact_update_failed(payment: StripePaymentData) -> dict:
    """Marca el contacto cuando un pago falla."""
    return {"hs_lead_status": "UNQUALIFIED"}
