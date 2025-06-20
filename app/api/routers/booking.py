import ssl
import hmac, hashlib, time
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.api.services.booking import record_booking
from app.schemas.booking import BookingPayload, BookingCreate

ssl._create_default_https_context = ssl._create_unverified_context

CALENDLY_SIGNING_KEY = settings.CALENDLY_SIGNING_KEY  # <-- NOT the PAT
TS_TOLERANCE_SEC = 3 * 60                             # 3-minute skew

router = APIRouter(tags=["booking"])

@router.post("/webhook/booking")
async def booking_webhook(
    request: Request,
    req: BookingPayload,
    db: AsyncSession = Depends(get_db),
    x_calendly_signature: str = Header(...),
):
    raw_body = await request.body()

    try:
        sig_parts = dict(kv.split("=", 1) for kv in x_calendly_signature.split(","))
        ts   = int(sig_parts["t"])
        sent = sig_parts["v1"]
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed signature header")

    if abs(time.time() - ts) > TS_TOLERANCE_SEC:
        raise HTTPException(status_code=400, detail="Signature timestamp too old")

    msg = f"{ts}.{raw_body.decode()}".encode()

    good = hmac.new(
        CALENDLY_SIGNING_KEY.encode(),
        msg,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(good, sent):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Calendly signature",
        )

    data = req.payload
    booking = BookingCreate(
        shop_id    = data["invitee"]["event_type"]["slug"],
        email      = data["invitee"]["email"],
        start_time = data["invitee"]["event"]["start_time"]
    )
    await record_booking(db, booking)
    return {"status": "ok"}
