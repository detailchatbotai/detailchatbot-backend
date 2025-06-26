from pydantic import BaseModel, constr
from typing import Optional

class SubscribeRequest(BaseModel):
    plan: constr(min_length=3, max_length=50)

class SubscribeResponse(BaseModel):
    checkout_url: Optional[str] = None
    plan: Optional[str] = None
    is_subscribed: Optional[bool] = None
    message: Optional[str] = None

class CancelRequest(BaseModel):
    # Optionally include a reason or other fields
    pass

class CancelResponse(BaseModel):
    success: bool
    message: Optional[str] = None

