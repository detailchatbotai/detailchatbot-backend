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
    # 1. Raw bytes exactly as Calendly sent them
    raw_body = await request.body()

    # 2. Split header → {'t': '1729330186', 'v1': '7f3c2d…'}
    try:
        sig_parts = dict(kv.split("=", 1) for kv in x_calendly_signature.split(","))
        ts   = int(sig_parts["t"])
        sent = sig_parts["v1"]
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed signature header")

    # 3. Optional: reject if timestamp is too old
    if abs(time.time() - ts) > TS_TOLERANCE_SEC:
        raise HTTPException(status_code=400, detail="Signature timestamp too old")

    # 4. Re-create the exact message Calendly signed
    msg = f"{ts}.{raw_body.decode()}".encode()

    # 5. Compute HMAC-SHA256 and compare
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

    # ---- Verified! process payload normally ----
    data = req.payload
    booking = BookingCreate(
        shop_id    = data["invitee"]["event_type"]["slug"],
        email      = data["invitee"]["email"],
        start_time = data["invitee"]["event"]["start_time"]
    )
    await record_booking(db, booking)
    return {"status": "ok"}
