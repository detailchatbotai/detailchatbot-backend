from pydantic import BaseModel, constr
from typing import Optional

class SubscriptionRequest(BaseModel):
    plan: constr(min_length=3, max_length=50)
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

class SubscriptionResponse(BaseModel):
    checkout_url: str
    session_id: str

class CancelSubscriptionRequest(BaseModel):
    # Optionally, allow passing a reason or other metadata
    reason: str | None = None

class CancelSubscriptionResponse(BaseModel):
    cancelled: bool
    message: str
