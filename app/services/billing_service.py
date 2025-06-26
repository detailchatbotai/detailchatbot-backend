from sqlalchemy.ext.asyncio import AsyncSession
from app.services.stripe_service import StripeService, StripeServiceException
from app.models.user import User
from app.repositories.user_repository import UserRepository
from typing import Optional
import logging

class BillingServiceException(Exception):
    pass

class BillingService:
    _logger = logging.getLogger(__name__)
    _stripe = StripeService()

    @staticmethod
    async def get_user(db: AsyncSession, *, email: Optional[str] = None, supabase_user_id: Optional[str] = None, subscription_id: Optional[str] = None) -> User:
        # Try all lookup methods in order, return first found
        if supabase_user_id:
            user_obj = await UserRepository.get_by_supabase_user_id(db, supabase_user_id)
            if user_obj:
                return user_obj
        if email:
            user_obj = await UserRepository.get_by_email(db, email)
            if user_obj:
                return user_obj
        if subscription_id:
            user_obj = await UserRepository.get_by_subscription_id(db, subscription_id)
            if user_obj:
                return user_obj
        BillingService._logger.error(f"User not found for email: {email}, supabase_user_id: {supabase_user_id}, subscription_id: {subscription_id}")
        raise BillingServiceException("User not found")

    @classmethod
    async def subscribe_user(
        cls,
        db: AsyncSession,
        email: str,
        plan: str,
        success_url: Optional[str],
        cancel_url: Optional[str]
    ) -> dict:
        user_obj = await cls.get_user(db, email=email)
        try:
            return await cls._stripe.create_checkout_session(
                plan=plan,
                customer_email=user_obj.email,
                success_url=success_url or "http://localhost:3000/success",
                cancel_url=cancel_url or "http://localhost:3000/cancel",
                supabase_user_id=user_obj.supabase_user_id
            )
        except StripeServiceException as exc:
            cls._logger.error(f"Stripe error: {exc}")
            raise BillingServiceException(str(exc))

    @classmethod
    async def update_subscription_status(
        cls,
        db: AsyncSession,
        *,
        supabase_user_id: Optional[str] = None,
        email: Optional[str] = None,
        subscription_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        is_subscribed: Optional[bool] = None
    ) -> None:
        user_obj = await cls.get_user(db, supabase_user_id=supabase_user_id, email=email, subscription_id=subscription_id)
        before = {
            'stripe_subscription_id': user_obj.stripe_subscription_id,
            'stripe_customer_id': user_obj.stripe_customer_id,
            'is_subscribed': user_obj.is_subscribed
        }
        if subscription_id is not None:
            user_obj.stripe_subscription_id = subscription_id
        if customer_id is not None:
            user_obj.stripe_customer_id = customer_id
        if is_subscribed is not None:
            user_obj.is_subscribed = is_subscribed
        after = {
            'stripe_subscription_id': user_obj.stripe_subscription_id,
            'stripe_customer_id': user_obj.stripe_customer_id,
            'is_subscribed': user_obj.is_subscribed
        }
        cls._logger.info(f"Updating user {user_obj.email}: before={before}, after={after}")
        await db.commit()

    @classmethod
    async def cancel_subscription(
        cls,
        db: AsyncSession,
        email: str,
        reason: Optional[str] = None
    ) -> dict:
        user_obj = await cls.get_user(db, email=email)
        if not user_obj.stripe_subscription_id:
            cls._logger.error(f"No active subscription for user: {email}")
            raise BillingServiceException("No active subscription to cancel")
        try:
            await cls._stripe.cancel_subscription(user_obj.stripe_subscription_id)
            user_obj.stripe_subscription_id = None
            user_obj.is_subscribed = False
            await db.commit()
            cls._logger.info(f"Subscription cancelled for user: {email}")
            return {"cancelled": True, "message": "Subscription cancelled successfully."}
        except StripeServiceException as exc:
            cls._logger.error(f"Stripe error on cancel: {exc}")
            raise BillingServiceException(str(exc))

