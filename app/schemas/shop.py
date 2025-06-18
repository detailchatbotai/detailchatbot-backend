from pydantic import BaseModel, ConfigDict
from typing import Dict

class ShopCreate(BaseModel):
    id: str
    name: str
    services: Dict[str, float]
    booking_link: str

class ShopRead(ShopCreate):
    is_active: bool
    plan_tier: str

    model_config = ConfigDict(from_attributes=True)
