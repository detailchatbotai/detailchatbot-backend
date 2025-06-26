import stripe
import logging
from app.core.config import settings
from typing import Optional, Dict
import asyncio

class StripeServiceException(Exception):
    """Custom exception for Stripe service errors."""
    pass

class StripeService:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.logger = logging.getLogger(__name__)
        self.price_map = {
            "starter": settings.STRIPE_PRICE_STARTER,
            # Add more plans as needed, e.g.:
            # "pro": settings.STRIPE_PRICE_PRO,
            # "elite": settings.STRIPE_PRICE_ELITE,
        }

    async def create_checkout_session(
        self,
        *,
        plan: str,
        customer_email: str,
        success_url: str,
        cancel_url: str,
        supabase_user_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create a Stripe Checkout session for a subscription plan.
        Uses run_in_executor to avoid blocking the event loop.
        Passes supabase_user_id as client_reference_id for robust webhook matching.
        """
        price_id = self._get_price_id(plan)
        loop = asyncio.get_event_loop()
        try:
            session = await loop.run_in_executor(
                None,
                lambda: stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    mode="subscription",
                    line_items=[{"price": price_id, "quantity": 1}],
                    customer_email=customer_email,
                    success_url=success_url,
                    cancel_url=cancel_url,
                    client_reference_id=supabase_user_id
                )
            )
            self.logger.info(f"Stripe checkout session created for {customer_email} plan {plan}")
            return {"checkout_url": session.url, "session_id": session.id}
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe API error: {e.user_message or str(e)}")
            raise StripeServiceException(e.user_message or "Stripe API error")
        except Exception as e:
            self.logger.error(f"Unexpected error creating Stripe session: {e}")
            raise StripeServiceException("Failed to create Stripe checkout session")

    async def cancel_subscription(self, subscription_id: str) -> None:
        """
        Cancel a Stripe subscription by ID.
        """
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(
                None,
                lambda: stripe.Subscription.delete(subscription_id)
            )
        except stripe.error.StripeError as e:
            self.logger.error(f"Stripe API error on cancel: {e.user_message or str(e)}")
            raise StripeServiceException(e.user_message or "Stripe API error")
        except Exception as e:
            self.logger.error(f"Unexpected error cancelling Stripe subscription: {e}")
            raise StripeServiceException("Failed to cancel Stripe subscription")

    def _get_price_id(self, plan: str) -> str:
        """
        Map plan name to Stripe price ID. Raise if not found.
        """
        price_id = self.price_map.get(plan)
        if not price_id:
            self.logger.error(f"Invalid plan selected: {plan}")
            raise StripeServiceException("Invalid plan selected")
        return price_id
