"""
Plans and subscription router for managing billing and subscription plans.
Handles plan listing, subscription creation, billing management, and usage tracking.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.stripe_service import StripeService, get_stripe_service
from app.core.dependencies import (
    get_verified_user,
    get_user_shop,
    rate_limit_general,
    VerifiedUser,
    UserShop
)
from app.models.plan import Plan
from app.models.shop import Shop
from app.core.security import SecurityHeaders
from app.core.config import settings
from app.schemas.plan import (
    SubscriptionRequest,
    PlanResponse,
    PlansListResponse,
    CheckoutResponse,
    SubscriptionResponse,
    UsageResponse,
    BillingPortalResponse,
    MessageResponse
)


router = APIRouter()



def format_plan_response(plan: Plan) -> PlanResponse:
    """Format plan object for API response"""
    # Calculate yearly savings
    yearly_savings = None
    if plan.price_yearly > 0 and plan.price_monthly > 0:
        yearly_total = plan.price_monthly * 12
        yearly_savings = round(yearly_total - plan.price_yearly, 2)
    
    # Determine if this is a popular plan (you can customize this logic)
    popular = plan.name.lower() in ["pro", "professional", "premium"]
    
    return PlanResponse(
        id=plan.id,
        name=plan.name,
        description=plan.description,
        price_monthly=plan.price_monthly,
        price_yearly=plan.price_yearly,
        max_chats_per_month=plan.max_chats_per_month,
        max_services=plan.max_services,
        features=plan.features or [],
        is_active=plan.is_active,
        yearly_savings=yearly_savings,
        popular=popular
    )


@router.get(
    "/",
    response_model=PlansListResponse,
    summary="Get available plans",
    description="Get list of all available subscription plans"
)
async def get_plans(
    current_user: VerifiedUser,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Get list of all available subscription plans"""
    try:
        # Get all active plans
        plans = db.query(Plan).filter(Plan.is_active == True).order_by(Plan.price_monthly).all()
        
        plan_responses = [format_plan_response(plan) for plan in plans]
        
        # Get current plan if user has a shop
        current_plan = None
        user_shops = current_user.shops
        if user_shops and user_shops[0].plan:
            current_plan = format_plan_response(user_shops[0].plan)
        
        return PlansListResponse(
            plans=plan_responses,
            current_plan=current_plan
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plans"
        )


@router.post(
    "/subscribe",
    response_model=CheckoutResponse,
    summary="Create subscription",
    description="Create a checkout session to subscribe to a plan"
)
async def create_subscription(
    subscription_data: SubscriptionRequest,
    shop: UserShop,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Create a checkout session to subscribe to a plan"""
    stripe_service = get_stripe_service(db)
    
    try:
        # Get the requested plan
        plan = db.query(Plan).filter(
            Plan.id == subscription_data.plan_id,
            Plan.is_active == True
        ).first()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        
        # Check if shop already has an active subscription
        if shop.subscription_status == "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shop already has an active subscription. Use upgrade/downgrade instead."
            )
        
        # Development mode: Check if Stripe is configured
        if settings.STRIPE_SECRET_KEY == "sk_test_placeholder_add_real_key" or not settings.STRIPE_SECRET_KEY:
            # Mock response for development
            return CheckoutResponse(
                checkout_session_id="cs_dev_mock_session_12345",
                checkout_url=f"{settings.FRONTEND_URL}/dev-payment-mock?plan={plan.name}&price=${plan.price_monthly}"
            )
        
        # Create checkout session
        checkout_data = await stripe_service.create_checkout_session(
            shop=shop,
            plan=plan,
            billing_cycle=subscription_data.billing_cycle,
            success_url=subscription_data.success_url,
            cancel_url=subscription_data.cancel_url
        )
        
        return CheckoutResponse(
            checkout_session_id=checkout_data["checkout_session_id"],
            checkout_url=checkout_data["checkout_url"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription"
        )


@router.get(
    "/current",
    response_model=SubscriptionResponse,
    summary="Get current subscription",
    description="Get current subscription details for the shop"
)
async def get_current_subscription(
    shop: UserShop,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Get current subscription details for the shop"""
    stripe_service = get_stripe_service(db)
    
    try:
        # Get subscription details from Stripe
        subscription_details = await stripe_service.get_subscription_details(shop)
        
        if subscription_details:
            return SubscriptionResponse(**subscription_details)
        else:
            # No active subscription, return shop status
            return SubscriptionResponse(
                status=shop.subscription_status,
                cancel_at_period_end=False
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve subscription details"
        )


@router.get(
    "/usage",
    response_model=UsageResponse,
    summary="Get usage statistics",
    description="Get current usage statistics for the shop"
)
async def get_usage_statistics(
    shop: UserShop,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Get current usage statistics for the shop"""
    try:
        from datetime import datetime, timezone
        from dateutil.relativedelta import relativedelta
        
        # Calculate current billing period (simplified - in production, use actual subscription period)
        now = datetime.now(timezone.utc)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = period_start + relativedelta(months=1)
        
        # Get plan limits
        plan = shop.plan
        chats_limit = plan.max_chats_per_month if plan else 100
        services_limit = plan.max_services if plan else 5
        
        # Get actual usage (simplified - in production, query analytics tables)
        # For now, return mock data - you'll need to implement actual usage tracking
        chats_used = 0  # TODO: Query actual chat usage from analytics
        services_used = len(shop.services) if shop.services else 0
        
        # Calculate usage percentages
        chats_percentage = (chats_used / chats_limit * 100) if chats_limit > 0 else 0
        services_percentage = (services_used / services_limit * 100) if services_limit > 0 else 0
        
        return UsageResponse(
            current_period_start=period_start.isoformat(),
            current_period_end=period_end.isoformat(),
            chats_used=chats_used,
            chats_limit=chats_limit,
            services_used=services_used,
            services_limit=services_limit,
            usage_percentage={
                "chats": round(chats_percentage, 1),
                "services": round(services_percentage, 1)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage statistics"
        )


@router.post(
    "/billing-portal",
    response_model=BillingPortalResponse,
    summary="Get billing portal",
    description="Get URL to Stripe customer billing portal"
)
async def get_billing_portal(
    shop: UserShop,
    return_url: Optional[str] = Query(None, description="URL to return to after portal session"),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Get URL to Stripe customer billing portal"""
    stripe_service = get_stripe_service(db)
    
    try:
        # Development mode: Check if Stripe is configured
        if settings.STRIPE_SECRET_KEY == "sk_test_placeholder_add_real_key" or not settings.STRIPE_SECRET_KEY:
            # Mock response for development
            return BillingPortalResponse(
                portal_url=f"{settings.FRONTEND_URL}/dev-billing-mock?shop={shop.name}"
            )
        
        portal_data = await stripe_service.create_customer_portal_session(
            shop=shop,
            return_url=return_url
        )
        
        return BillingPortalResponse(
            portal_url=portal_data["portal_url"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create billing portal session"
        )


@router.post(
    "/cancel",
    response_model=MessageResponse,
    summary="Cancel subscription",
    description="Cancel the current subscription"
)
async def cancel_subscription(
    shop: UserShop,
    immediately: bool = Query(False, description="Cancel immediately or at period end"),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Cancel the current subscription"""
    stripe_service = get_stripe_service(db)
    
    try:
        if shop.subscription_status not in ["active", "trialing"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active subscription to cancel"
            )
        
        success = await stripe_service.cancel_subscription(
            shop=shop,
            immediately=immediately
        )
        
        if success:
            if immediately:
                message = "Subscription cancelled immediately"
            else:
                message = "Subscription will be cancelled at the end of the current billing period"
            
            return MessageResponse(message=message)
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel subscription"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )


@router.post(
    "/upgrade",
    response_model=CheckoutResponse,
    summary="Upgrade/change plan",
    description="Upgrade or change to a different plan"
)
async def upgrade_plan(
    subscription_data: SubscriptionRequest,
    shop: UserShop,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Upgrade or change to a different plan"""
    stripe_service = get_stripe_service(db)
    
    try:
        # Get the requested plan
        plan = db.query(Plan).filter(
            Plan.id == subscription_data.plan_id,
            Plan.is_active == True
        ).first()
        
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Plan not found"
            )
        
        # Check if it's a different plan
        if shop.plan_id == plan.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shop is already on this plan"
            )
        
        # Development mode: Check if Stripe is configured
        if settings.STRIPE_SECRET_KEY == "sk_test_placeholder_add_real_key" or not settings.STRIPE_SECRET_KEY:
            # Mock response for development
            return CheckoutResponse(
                checkout_session_id="cs_dev_upgrade_mock_12345",
                checkout_url=f"{settings.FRONTEND_URL}/dev-payment-mock?plan={plan.name}&price=${plan.price_monthly}&upgrade=true"
            )
        
        # For simplicity, create a new checkout session
        # In production, you might want to handle immediate plan changes for existing subscriptions
        checkout_data = await stripe_service.create_checkout_session(
            shop=shop,
            plan=plan,
            billing_cycle=subscription_data.billing_cycle,
            success_url=subscription_data.success_url,
            cancel_url=subscription_data.cancel_url
        )
        
        return CheckoutResponse(
            checkout_session_id=checkout_data["checkout_session_id"],
            checkout_url=checkout_data["checkout_url"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upgrade plan"
        )


# Note: Security headers would be added at the app level in main.py
# APIRouter doesn't support middleware, only the main FastAPI app does