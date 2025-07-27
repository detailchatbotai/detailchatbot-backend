from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.openai_service import OpenAIService
from app.models.shop import Shop
from app.models.chat import ChatSession, ChatMessage
import uuid

router = APIRouter()


@router.post("/{shop_id}", response_model=ChatResponse)
async def chat_with_bot(
        shop_id: int,
        chat_request: ChatRequest,
        request: Request,
        db: Session = Depends(get_db)
):
    # Verify shop exists and is active
    shop = db.query(Shop).filter(Shop.id == shop_id, Shop.is_active == True).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    # Get or create chat session
    session_id = chat_request.session_id or str(uuid.uuid4())
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()

    if not session:
        session = ChatSession(
            session_id=session_id,
            shop_id=shop_id,
            customer_ip=request.client.host,
            customer_user_agent=request.headers.get("user-agent")
        )
        db.add(session)
        db.commit()

    # Save customer message
    customer_message = ChatMessage(
        session_id=session.id,
        message=chat_request.message,
        is_from_customer=True
    )
    db.add(customer_message)

    # Generate AI response
    openai_service = OpenAIService(db)
    ai_response = await openai_service.generate_response(
        shop=shop,
        message=chat_request.message,
        session=session
    )

    # Save AI response
    ai_message = ChatMessage(
        session_id=session.id,
        message=ai_response.message,
        is_from_customer=False,
        openai_tokens_used=ai_response.tokens_used,
        openai_model=ai_response.model
    )
    db.add(ai_message)
    db.commit()

    return ChatResponse(
        message=ai_response.message,
        session_id=session_id,
        suggestions=ai_response.suggestions,
        booking_prompt=ai_response.booking_prompt,
        services_mentioned=ai_response.services_mentioned
    )