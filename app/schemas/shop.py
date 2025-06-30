from pydantic import BaseModel, constr
from typing import Optional
from datetime import datetime

class ShopBase(BaseModel):
    name: constr(min_length=2, max_length=100)
    services: Optional[str] = None
    pricing: Optional[str] = None
    hours: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None

class ShopCreate(ShopBase):
    pass

class ShopUpdate(BaseModel):
    services: Optional[str] = None
    pricing: Optional[str] = None
    hours: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None

class ShopRead(ShopBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

