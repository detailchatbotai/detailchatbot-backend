import stripe
from app.core.config import settings

class StripeClient:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.price_map = {
            "starter": settings.STRIPE_PRICE_STARTER,
            # "pro": settings.STRIPE_PRICE_PRO,
            # "elite": settings.STRIPE_PRICE_ELITE,
        }

    def get_price_id(self, plan: str) -> str:
        price_id = self.price_map.get(plan)
        if not price_id:
            raise ValueError(f"Invalid plan: {plan}")
        return price_id

    def create_customer(self, email: str, metadata: dict = None):
        return stripe.Customer.create(email=email, metadata=metadata or {})

    def retrieve_customer(self, customer_id: str):
        return stripe.Customer.retrieve(customer_id)

    def create_checkout_session(self, customer_id: str, price_id: str, success_url: str, cancel_url: str, metadata: dict = None):
        return stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata or {}
        )

    def cancel_subscription(self, subscription_id: str):
        return stripe.Subscription.delete(subscription_id)

    def construct_event(self, payload: bytes, sig_header: str, webhook_secret: str):
        return stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=webhook_secret
        )

stripe_client = StripeClient()

