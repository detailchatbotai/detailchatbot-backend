from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.services.billing_service import BillingService, BillingServiceException
import logging
import stripe

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)

@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        logger.error(f"Invalid Stripe webhook signature: {e}")
        return JSONResponse(status_code=400, content={"error": "Invalid signature"})

    event_type = event["type"]
    data = event["data"]["object"]

    # Map event types to update_subscription_status params
    event_map = {
        "checkout.session.completed": dict(
            supabase_user_id=data.get("client_reference_id"),
            email=data.get("customer_email"),
            subscription_id=data.get("subscription"),
            customer_id=data.get("customer"),
            is_subscribed=True
        ),
        "customer.subscription.deleted": dict(
            subscription_id=data.get("id"),
            is_subscribed=False
        ),
    }

    params = event_map.get(event_type)
    if params:
        try:
            await BillingService.update_subscription_status(db, **params)
        except BillingServiceException as exc:
            logger.error(f"BillingService error in webhook: {exc}")
            return JSONResponse(status_code=400, content={"error": str(exc)})
        except Exception as exc:
            logger.error(f"Unexpected error in webhook: {exc}")
            return JSONResponse(status_code=500, content={"error": "Internal server error"})

    return {"status": "success"}
