from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.billing_service import BillingService
from app.schemas.billing import SubscribeRequest, SubscribeResponse, CancelRequest, CancelResponse
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/billing", tags=["billing"])

@router.post("/subscribe", response_model=SubscribeResponse)
async def subscribe(
    data: SubscribeRequest,
    db: AsyncSession = Depends(get_db),
    supabase_user_id: str = Depends(AuthService.get_current_user_supabase_id)
):
    """
    Initiate a Stripe Checkout session for the selected plan.
    Returns a Stripe Checkout URL for the frontend to redirect the user.
    """
    return await BillingService.create_checkout_session(db, supabase_user_id, data.plan)

@router.post("/cancel", response_model=CancelResponse)
async def cancel_subscription(
    data: CancelRequest,
    db: AsyncSession = Depends(get_db),
    supabase_user_id: str = Depends(AuthService.get_current_user_supabase_id)
):
    """
    Cancel the user's active Stripe subscription.
    """
    return await BillingService.cancel_subscription(db, supabase_user_id)

@router.get("/status", response_model=SubscribeResponse)
async def subscription_status(
    db: AsyncSession = Depends(get_db),
    supabase_user_id: str = Depends(AuthService.get_current_user_supabase_id)
):
    """
    Get the current subscription status and plan for the authenticated user.
    """
    return await BillingService.get_subscription_status(db, supabase_user_id)

