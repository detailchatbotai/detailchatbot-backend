from pydantic import BaseModel, ConfigDict
from typing import Literal

class CheckoutRequest(BaseModel):
    shop_id: str
    plan_tier: Literal["starter"]

class CheckoutResponse(BaseModel):
    url: str
    model_config = ConfigDict(from_attributes=True)
