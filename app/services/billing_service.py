from app.services.stripe_client import stripe_client
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
import logging

logger = logging.getLogger(__name__)

class BillingService:
    @staticmethod
    async def create_checkout_session(db: AsyncSession, supabase_user_id: str, plan: str) -> dict:
        """
        Create a Stripe Checkout session for the selected plan and return the session URL.
        """
        user = await UserRepository.get_by_supabase_user_id(db, supabase_user_id)
        if not user:
            logger.error(f"User not found for supabase_user_id: {supabase_user_id}")
            raise Exception("User not found")

        # Create Stripe customer if needed
        if not user.stripe_customer_id:
            customer = stripe_client.create_customer(
                email=user.email,
                metadata={"supabase_user_id": supabase_user_id}
            )
            user.stripe_customer_id = customer.id
            await db.commit()
            await db.refresh(user)
        else:
            customer = stripe_client.retrieve_customer(user.stripe_customer_id)

        # Get the correct Stripe price ID for the plan
        try:
            price_id = stripe_client.get_price_id(plan)
        except ValueError as e:
            logger.error(str(e))
            raise Exception(str(e))

        # Create Stripe Checkout session
        session = stripe_client.create_checkout_session(
            customer_id=customer.id,
            price_id=price_id,
            success_url=settings.SUCCESS_URL,
            cancel_url=settings.CANCEL_URL,
            metadata={"supabase_user_id": supabase_user_id, "plan": plan}
        )
        return {"checkout_url": session.url, "plan": plan, "is_subscribed": user.is_subscribed}

    @staticmethod
    async def cancel_subscription(db: AsyncSession, supabase_user_id: str) -> dict:
        """
        Cancel the user's active Stripe subscription and update DB.
        """
        user = await UserRepository.get_by_supabase_user_id(db, supabase_user_id)
        if not user or not user.stripe_subscription_id:
            logger.error(f"No active subscription for user: {supabase_user_id}")
            return {"success": False, "message": "No active subscription found."}
        try:
            stripe_client.cancel_subscription(user.stripe_subscription_id)
            user.is_subscribed = False
            user.plan = "starter"
            user.stripe_subscription_id = None
            await db.commit()
            await db.refresh(user)
            return {"success": True, "message": "Subscription cancelled."}
        except Exception as e:
            logger.error(f"Stripe cancellation failed: {e}")
            return {"success": False, "message": str(e)}

    @staticmethod
    async def get_subscription_status(db: AsyncSession, supabase_user_id: str) -> dict:
        """
        Return the user's current subscription status and plan.
        """
        user = await UserRepository.get_by_supabase_user_id(db, supabase_user_id)
        if not user:
            logger.error(f"User not found for supabase_user_id: {supabase_user_id}")
            raise Exception("User not found")
        return {"plan": user.plan, "is_subscribed": user.is_subscribed}

    @staticmethod
    async def handle_stripe_event(event: Any) -> None:
        """
        Handle incoming Stripe webhook events (e.g., checkout.session.completed, customer.subscription.updated).
        Update user subscription status in DB as needed.
        """
        # Example: handle checkout.session.completed
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            supabase_user_id = session["metadata"].get("supabase_user_id")
            subscription_id = session.get("subscription")
            plan = session["metadata"].get("plan")
            # Fetch user and update subscription info
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                user = await UserRepository.get_by_supabase_user_id(db, supabase_user_id)
                if user:
                    user.is_subscribed = True
                    user.plan = plan
                    user.stripe_subscription_id = subscription_id
                    await db.commit()
        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            subscription_id = subscription["id"]
            from app.core.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                user = await UserRepository.get_by_subscription_id(db, subscription_id)
                if user:
                    user.is_subscribed = False
                    user.plan = "starter"
                    user.stripe_subscription_id = None
                    await db.commit()
        # Add more event types as needed
