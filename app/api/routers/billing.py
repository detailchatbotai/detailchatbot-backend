from fastapi import APIRouter, HTTPException
from app.schemas.billing import CheckoutRequest, CheckoutResponse
from app.api.services.billing import create_checkout_session

router = APIRouter(tags=["billing"], prefix="/api")

@router.post(
    "/create-checkout-session",
    response_model=CheckoutResponse
)
async def checkout(req: CheckoutRequest):
    try:
        # Pass both shop_id and plan_tier
        url = create_checkout_session(req.shop_id, req.plan_tier)
        return CheckoutResponse(url=url)
    except Exception as e:
        raise HTTPException(400, f"Stripe error: {e}")
