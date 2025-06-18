import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(shop_id: str, plan_tier: str) -> str:
    price_map = {
        "starter": settings.STRIPE_PRICE_STARTER,
        # "pro":     settings.STRIPE_PRICE_PRO,
        # "elite":   settings.STRIPE_PRICE_ELITE,
    }
    price_id = price_map.get(plan_tier.lower())
    if not price_id:
        raise ValueError(f"Unknown plan_tier: {plan_tier}")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.SUCCESS_URL}?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=settings.CANCEL_URL,
        metadata={"shop_id": shop_id, "plan_tier": plan_tier},
    )
    return session.url
