from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Any, Dict
from datetime import datetime

class BookingPayload(BaseModel):
    event: str
    payload: Dict[str, Any]

    model_config = ConfigDict(from_attributes=True)

class BookingCreate(BaseModel):
    shop_id: str
    email: EmailStr
    start_time: datetime

    model_config = ConfigDict(from_attributes=True)
