from app.services.stripe_client import stripe_client
from app.core.config import settings


def verify_stripe_signature(payload: bytes, sig_header: str) -> dict:
    """
    Verify the Stripe webhook signature and return the event object using the Stripe client.
    Raises Exception if invalid.
    """
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    try:
        event = stripe_client.construct_event(payload, sig_header, webhook_secret)
        return event
    except Exception as e:
        raise Exception(f"Invalid Stripe signature: {e}")
