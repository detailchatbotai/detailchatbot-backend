"""
Stripe service for handling subscription billing and payment processing.
Manages customer creation, subscriptions, checkouts, and webhook processing.
"""

import logging
import stripe
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.shop import Shop
from app.models.user import User
from app.models.plan import Plan
from app.core.config import settings


logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service class for handling Stripe operations"""
    
    def __init__(self, db: Session):
        self.db = db
        
        if not settings.STRIPE_SECRET_KEY:
            logger.warning("Stripe secret key not configured - payment functionality disabled")
    
    async def create_customer(self, user: User, shop: Shop) -> str:
        """
        Create a Stripe customer for a user/shop.
        
        Args:
            user: User object
            shop: Shop object
            
        Returns:
            Stripe customer ID
            
        Raises:
            HTTPException: If customer creation fails
        """
        if not settings.STRIPE_SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment processing not available"
            )
        
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=shop.name,
                metadata={
                    "user_id": str(user.id),
                    "shop_id": str(shop.id),
                    "shop_name": shop.name
                }
            )
            
            # Update shop with Stripe customer ID
            shop.stripe_customer_id = customer.id
            self.db.commit()
            
            logger.info(f"Stripe customer created: {customer.id} for shop {shop.id}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment customer"
            )
        except Exception as e:
            logger.error(f"Unexpected error creating Stripe customer: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment setup failed"
            )
    
    async def create_checkout_session(
        self,
        shop: Shop,
        plan: Plan,
        billing_cycle: str = "monthly",
        success_url: str = None,
        cancel_url: str = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for subscription.
        
        Args:
            shop: Shop to subscribe
            plan: Plan to subscribe to
            billing_cycle: "monthly" or "yearly"
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect after cancelled payment
            
        Returns:
            Dict with checkout session data
            
        Raises:
            HTTPException: If checkout session creation fails
        """
        if not settings.STRIPE_SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment processing not available"
            )
        
        # Ensure shop has a Stripe customer
        if not shop.stripe_customer_id:
            customer_id = await self.create_customer(shop.owner, shop)
        else:
            customer_id = shop.stripe_customer_id
        
        # Handle free plans (no Stripe checkout needed)
        if plan.price_monthly == 0 and plan.price_yearly == 0:
            # Free plan - just activate subscription directly
            shop.subscription_status = "active"
            shop.plan_id = plan.id
            self.db.commit()
            
            # Return mock checkout data for consistency
            return {
                "checkout_session_id": f"free_plan_{shop.id}_{plan.id}",
                "checkout_url": f"{settings.FRONTEND_URL}/dashboard/billing/success?free_plan=true",
                "customer_id": customer_id
            }
        
        # Get the appropriate price ID for paid plans
        if billing_cycle == "yearly":
            price_id = plan.stripe_price_id_yearly
        else:
            price_id = plan.stripe_price_id_monthly
        
        if not price_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan {plan.name} not available for {billing_cycle} billing"
            )
        
        # Set default URLs if not provided
        if not success_url:
            success_url = f"{settings.FRONTEND_URL}/dashboard/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
        if not cancel_url:
            cancel_url = f"{settings.FRONTEND_URL}/dashboard/billing/cancelled"
        
        try:
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "shop_id": str(shop.id),
                    "plan_id": str(plan.id),
                    "billing_cycle": billing_cycle
                },
                allow_promotion_codes=True,
                billing_address_collection='required',
                customer_update={
                    'address': 'auto',
                    'name': 'auto'
                }
            )
            
            logger.info(f"Checkout session created: {checkout_session.id} for shop {shop.id}")
            
            return {
                "checkout_session_id": checkout_session.id,
                "checkout_url": checkout_session.url,
                "customer_id": customer_id
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create payment session"
            )
        except Exception as e:
            logger.error(f"Unexpected error creating checkout session: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment setup failed"
            )
    
    async def create_customer_portal_session(
        self,
        shop: Shop,
        return_url: str = None
    ) -> Dict[str, str]:
        """
        Create a Stripe customer portal session for subscription management.
        
        Args:
            shop: Shop object
            return_url: URL to return to after portal session
            
        Returns:
            Dict with portal session URL
        """
        if not settings.STRIPE_SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment processing not available"
            )
        
        if not shop.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No payment customer found"
            )
        
        if not return_url:
            return_url = f"{settings.FRONTEND_URL}/dashboard/billing"
        
        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=shop.stripe_customer_id,
                return_url=return_url,
            )
            
            logger.info(f"Customer portal session created for shop {shop.id}")
            
            return {
                "portal_url": portal_session.url
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal session: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create billing portal session"
            )
    
    async def get_subscription_details(self, shop: Shop) -> Optional[Dict[str, Any]]:
        """
        Get current subscription details for a shop.
        
        Args:
            shop: Shop object
            
        Returns:
            Dict with subscription details or None if no subscription
        """
        if not settings.STRIPE_SECRET_KEY or not shop.stripe_customer_id:
            return None
        
        try:
            # Get customer's subscriptions
            subscriptions = stripe.Subscription.list(
                customer=shop.stripe_customer_id,
                status='all',
                limit=10
            )
            
            # Find the most recent active subscription
            active_subscription = None
            for sub in subscriptions.data:
                if sub.status in ['active', 'trialing', 'past_due']:
                    active_subscription = sub
                    break
            
            if not active_subscription:
                return None
            
            # Get plan details
            plan_id = active_subscription.metadata.get('plan_id')
            plan = None
            if plan_id:
                plan = self.db.query(Plan).filter(Plan.id == int(plan_id)).first()
            
            return {
                "subscription_id": active_subscription.id,
                "status": active_subscription.status,
                "current_period_start": datetime.fromtimestamp(
                    active_subscription.current_period_start, tz=timezone.utc
                ).isoformat(),
                "current_period_end": datetime.fromtimestamp(
                    active_subscription.current_period_end, tz=timezone.utc
                ).isoformat(),
                "cancel_at_period_end": active_subscription.cancel_at_period_end,
                "plan": {
                    "id": plan.id if plan else None,
                    "name": plan.name if plan else "Unknown",
                    "price": active_subscription.items.data[0].price.unit_amount / 100,
                    "currency": active_subscription.items.data[0].price.currency,
                    "interval": active_subscription.items.data[0].price.recurring.interval
                } if plan else None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error getting subscription details: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting subscription details: {e}")
            return None
    
    async def cancel_subscription(
        self,
        shop: Shop,
        immediately: bool = False
    ) -> bool:
        """
        Cancel a shop's subscription.
        
        Args:
            shop: Shop object
            immediately: Whether to cancel immediately or at period end
            
        Returns:
            True if cancellation successful
        """
        if not settings.STRIPE_SECRET_KEY or not shop.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription found"
            )
        
        try:
            # Find active subscription
            subscriptions = stripe.Subscription.list(
                customer=shop.stripe_customer_id,
                status='active',
                limit=1
            )
            
            if not subscriptions.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No active subscription found"
                )
            
            subscription = subscriptions.data[0]
            
            if immediately:
                # Cancel immediately
                stripe.Subscription.delete(subscription.id)
                shop.subscription_status = "cancelled"
                logger.info(f"Subscription cancelled immediately for shop {shop.id}")
            else:
                # Cancel at period end
                stripe.Subscription.modify(
                    subscription.id,
                    cancel_at_period_end=True
                )
                logger.info(f"Subscription set to cancel at period end for shop {shop.id}")
            
            self.db.commit()
            return True
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel subscription"
            )
    
    async def process_webhook_event(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """
        Process Stripe webhook events.
        
        Args:
            payload: Webhook payload
            sig_header: Stripe signature header
            
        Returns:
            Dict with processing result
        """
        if not settings.STRIPE_WEBHOOK_SECRET:
            logger.warning("Stripe webhook secret not configured")
            return {"status": "ignored", "reason": "webhook_secret_not_configured"}
        
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Handle the event
        event_type = event['type']
        data_object = event['data']['object']
        
        logger.info(f"Processing webhook event: {event_type}")
        
        try:
            if event_type == 'checkout.session.completed':
                await self._handle_checkout_completed(data_object)
                
            elif event_type == 'customer.subscription.created':
                await self._handle_subscription_created(data_object)
                
            elif event_type == 'customer.subscription.updated':
                await self._handle_subscription_updated(data_object)
                
            elif event_type == 'customer.subscription.deleted':
                await self._handle_subscription_deleted(data_object)
                
            elif event_type == 'invoice.payment_succeeded':
                await self._handle_payment_succeeded(data_object)
                
            elif event_type == 'invoice.payment_failed':
                await self._handle_payment_failed(data_object)
                
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {"status": "ignored", "reason": "unhandled_event_type"}
            
            return {"status": "processed", "event_type": event_type}
            
        except Exception as e:
            logger.error(f"Error processing webhook {event_type}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook processing failed"
            )
    
    async def _handle_checkout_completed(self, session: Dict[str, Any]):
        """Handle successful checkout completion"""
        shop_id = session['metadata'].get('shop_id')
        if not shop_id:
            logger.warning("Checkout completed but no shop_id in metadata")
            return
        
        shop = self.db.query(Shop).filter(Shop.id == int(shop_id)).first()
        if not shop:
            logger.error(f"Shop {shop_id} not found for completed checkout")
            return
        
        # Update shop subscription status
        shop.subscription_status = "active"
        shop.stripe_customer_id = session['customer']
        self.db.commit()
        
        logger.info(f"Checkout completed for shop {shop_id}")
    
    async def _handle_subscription_created(self, subscription: Dict[str, Any]):
        """Handle subscription creation"""
        customer_id = subscription['customer']
        
        shop = self.db.query(Shop).filter(
            Shop.stripe_customer_id == customer_id
        ).first()
        
        if shop:
            shop.subscription_status = "active"
            self.db.commit()
            logger.info(f"Subscription created for shop {shop.id}")
    
    async def _handle_subscription_updated(self, subscription: Dict[str, Any]):
        """Handle subscription updates"""
        customer_id = subscription['customer']
        status = subscription['status']
        
        shop = self.db.query(Shop).filter(
            Shop.stripe_customer_id == customer_id
        ).first()
        
        if shop:
            # Map Stripe status to our status
            status_mapping = {
                'active': 'active',
                'trialing': 'trial',
                'past_due': 'past_due',
                'canceled': 'cancelled',
                'unpaid': 'cancelled'
            }
            
            shop.subscription_status = status_mapping.get(status, 'cancelled')
            self.db.commit()
            logger.info(f"Subscription updated for shop {shop.id}: {status}")
    
    async def _handle_subscription_deleted(self, subscription: Dict[str, Any]):
        """Handle subscription cancellation"""
        customer_id = subscription['customer']
        
        shop = self.db.query(Shop).filter(
            Shop.stripe_customer_id == customer_id
        ).first()
        
        if shop:
            shop.subscription_status = "cancelled"
            self.db.commit()
            logger.info(f"Subscription cancelled for shop {shop.id}")
    
    async def _handle_payment_succeeded(self, invoice: Dict[str, Any]):
        """Handle successful payment"""
        customer_id = invoice['customer']
        
        shop = self.db.query(Shop).filter(
            Shop.stripe_customer_id == customer_id
        ).first()
        
        if shop and shop.subscription_status in ['past_due', 'cancelled']:
            shop.subscription_status = "active"
            self.db.commit()
            logger.info(f"Payment succeeded for shop {shop.id}")
    
    async def _handle_payment_failed(self, invoice: Dict[str, Any]):
        """Handle failed payment"""
        customer_id = invoice['customer']
        
        shop = self.db.query(Shop).filter(
            Shop.stripe_customer_id == customer_id
        ).first()
        
        if shop:
            shop.subscription_status = "past_due"
            self.db.commit()
            logger.info(f"Payment failed for shop {shop.id}")


# Factory function for dependency injection
def get_stripe_service(db: Session) -> StripeService:
    """Factory function to create StripeService instance"""
    return StripeService(db)