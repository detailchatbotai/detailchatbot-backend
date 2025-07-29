from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import stripe
import json
from app.core.database import get_db
from app.core.config import settings
from app.models.shop import Shop
from app.services.stripe_service import StripeService

router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    stripe_service = StripeService(db)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await stripe_service.handle_successful_payment(session)

    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        await stripe_service.handle_subscription_renewal(invoice)

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        await stripe_service.handle_subscription_cancellation(subscription)

    return {"status": "success"}