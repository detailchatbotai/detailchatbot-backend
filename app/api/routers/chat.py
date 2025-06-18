from fastapi import APIRouter, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.api.services.chat import chat_echo

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Stub chat endpoint—simply echoes back the userMessage.
    """
    return await chat_echo(req.userMessage)
