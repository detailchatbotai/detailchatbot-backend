from fastapi import APIRouter, Depends, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.billing import SubscriptionRequest, SubscriptionResponse
from app.services.billing_service import BillingService, BillingServiceException
from app.core.database import get_db
from jose import jwt, JWTError
from app.core.config import settings
import logging

router = APIRouter(prefix="/billing", tags=["billing"])
logger = logging.getLogger(__name__)

SUPABASE_JWT_SECRET = settings.SUPABASE_JWT_SECRET

def get_email_from_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"], audience="authenticated")
        email = payload.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Email not found in token")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user_email(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header.split(" ", 1)[1]
    return get_email_from_token(token)

@router.post("/subscribe", response_model=SubscriptionResponse, status_code=status.HTTP_200_OK)
async def subscribe(
    request: SubscriptionRequest,
    db: AsyncSession = Depends(get_db),
    email: str = Depends(get_current_user_email),
) -> SubscriptionResponse:
    try:
        result = await BillingService.subscribe_user(
            db=db,
            email=email,
            plan=request.plan,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )
        return SubscriptionResponse(**result)
    except BillingServiceException as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("Unexpected error in /billing/subscribe")
        raise HTTPException(status_code=500, detail="Internal server error")
