from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime

class BookingPayload(BaseModel):
    event: str
    payload: dict

    model_config = ConfigDict(from_attributes=True)

class BookingCreate(BaseModel):
    shop_id: str
    email: EmailStr
    start_time: datetime
