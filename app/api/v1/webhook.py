from fastapi import APIRouter, Request, HTTPException, status
from app.services.billing_service import BillingService
from app.utils.stripe import verify_stripe_signature
from fastapi.responses import JSONResponse
import logging

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = logging.getLogger(__name__)

@router.post("/stripe", status_code=200)
async def stripe_webhook(request: Request):
    """
    Stripe webhook endpoint to handle subscription events (e.g., checkout.session.completed, customer.subscription.updated).
    Verifies Stripe signature and delegates event handling to BillingService.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = verify_stripe_signature(payload, sig_header)
    except Exception as e:
        logger.error(f"Stripe webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    await BillingService.handle_stripe_event(event)
    return JSONResponse(content={"status": "success"})

