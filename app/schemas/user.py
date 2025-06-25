from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    shop_name: constr(min_length=2, max_length=100)
    plan: constr(min_length=3, max_length=50) = "starter"
    is_subscribed: bool = False
    is_active: bool = True

class UserCreate(UserBase):
    password: constr(min_length=8, max_length=128)

class UserRead(UserBase):
    id: int
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=128)