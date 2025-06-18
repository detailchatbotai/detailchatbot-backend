from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.chat import ChatRequest, ChatResponse
from app.api.services.chat import chat_with_openai
from app.core.database import get_db

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    AI‐powered chat: uses OpenAI to answer user questions in the context of a shop.
    """
    return await chat_with_openai(req.userMessage, req.shopId, db)

# @router.post("/chat", response_model=ChatResponse)
# async def chat_endpoint(req: ChatRequest, db: AsyncSession = Depends(get_db)):
#     shop = await get_shop(db, req.shopId)
#     if not shop.is_active:
#         raise HTTPException(402, "Subscription required to chat")
#     return await chat_with_openai(req.userMessage, req.shopId, db)
