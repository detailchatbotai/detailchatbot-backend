"""
Chat router for handling AI chatbot interactions.
Provides clean API endpoints that delegate to ChatService for business logic.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse
from app.models.shop import Shop
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_chat_service(db: Session = Depends(get_db)) -> ChatService:
    """Dependency to provide ChatService instance"""
    return ChatService(db)


@router.post(
    "/{shop_api_key}",
    response_model=ChatResponse,
    summary="Send chat message",
    description="Send a message to the shop's AI chatbot"
)
async def chat_with_bot(
    shop_api_key: str,
    chat_request: ChatRequest,
    request: Request,
    db: Session = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Handle chat message from customer to shop's AI assistant"""
    
    try:
        # Verify shop exists and is active using API key for security
        shop = db.query(Shop).filter(
            Shop.public_api_key == shop_api_key,
            Shop.is_active == True
        ).first()
        
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found or inactive"
            )
        
        # Extract customer metadata
        customer_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Process chat message through service
        return await chat_service.process_chat_message(
            shop=shop,
            message=chat_request.message,
            session_id=chat_request.session_id,
            customer_ip=customer_ip,
            user_agent=user_agent
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error for shop {shop_api_key}: {e}")
        
        # Return graceful fallback using service
        return chat_service.create_fallback_response(chat_request.session_id)


@router.get(
    "/{shop_api_key}/history/{session_id}",
    response_model=ChatHistoryResponse,
    summary="Get chat history",
    description="Get conversation history for a chat session"
)
async def get_chat_history(
    shop_api_key: str,
    session_id: str,
    db: Session = Depends(get_db),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get chat history for a session"""
    
    try:
        # Verify shop
        shop = db.query(Shop).filter(
            Shop.public_api_key == shop_api_key,
            Shop.is_active == True
        ).first()
        
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found"
            )
        
        # Get chat history through service
        return await chat_service.get_chat_history(shop=shop, session_id=session_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )