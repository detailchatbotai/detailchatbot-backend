from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.chatbot_service import ChatbotService
from app.schemas.chatbot import ChatRequest, ChatResponse, UsageResponse

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

@router.post("/ask", response_model=ChatResponse)
async def ask_chatbot(
    data: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle a public user question for a specific shop, enforce plan/usage limits, and return an AI-generated answer.
    Requires a shop_name in the request.
    """
    if not hasattr(data, "shop_name") or not data.shop_name:
        raise HTTPException(status_code=400, detail="shop_name is required for public chatbot access.")
    return await ChatbotService.ask_public(db, data.shop_name, data.question)

@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    shop_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Return the shop's current AI query usage and plan limits.
    """
    return await ChatbotService.get_usage_public(db, shop_name)
