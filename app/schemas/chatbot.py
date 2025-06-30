from pydantic import BaseModel, constr
from typing import Optional

class ChatRequest(BaseModel):
    question: constr(min_length=1, max_length=1000)
    shop_name: constr(min_length=2, max_length=100)

class ChatResponse(BaseModel):
    answer: str
    usage: Optional[int] = None
    limit: Optional[int] = None
    plan: Optional[str] = None
    reached_limit: Optional[bool] = None

class UsageResponse(BaseModel):
    usage: int
    limit: int
    plan: str
    reached_limit: bool
