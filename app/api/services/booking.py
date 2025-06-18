import json
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.models.booking import Booking
from app.schemas.booking import BookingCreate
from app.core.config import settings

async def record_booking(db: AsyncSession, booking: BookingCreate):
    new = Booking(shop_id=booking.shop_id, timestamp=booking.start_time, customer_email=booking.email)
    db.add(new)

    # send confirmation email
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    msg = Mail(
        from_email=settings.SENDGRID_SENDER,
        to_emails=booking.email,
        subject="Your DetailChatBot Booking Confirmed",
        html_content=(
            f"Thanks for booking!<br>"
            f"Shop: {booking.shop_id}<br>"
            f"Time: {booking.start_time.isoformat()}"
        )
    )
    resp = sg.send(msg)
    if resp.status_code >= 400:
        raise HTTPException(500, "Failed to send confirmation email")
