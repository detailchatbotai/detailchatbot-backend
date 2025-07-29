"""
Chat service for managing customer chat sessions and AI interactions.
Handles session management, usage tracking, and chat flow orchestration.
"""

import logging
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.shop import Shop
from app.models.chat import ChatSession, ChatMessage
from app.services.openai_service import OpenAIService, AIResponse
from app.schemas.chat import ChatResponse, ChatHistoryResponse, ChatHistoryMessage

logger = logging.getLogger(__name__)


class ChatService:
    """Service for handling chat operations and business logic"""
    
    def __init__(self, db: Session):
        self.db = db
        self.openai_service = OpenAIService(db)
    
    async def process_chat_message(
        self,
        shop: Shop,
        message: str,
        session_id: Optional[str] = None,
        customer_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ChatResponse:
        """
        Process a chat message from customer to shop's AI assistant.
        
        Args:
            shop: Shop object
            message: Customer message
            session_id: Optional existing session ID
            customer_ip: Customer IP address
            user_agent: Customer user agent
            
        Returns:
            ChatResponse with AI response and metadata
            
        Raises:
            HTTPException: If processing fails
        """
        try:
            # Check usage limits
            if await self._is_usage_exceeded(shop):
                return self._create_usage_exceeded_response(session_id)
            
            # Get or create session
            session = await self._get_or_create_session(
                shop=shop,
                session_id=session_id,
                customer_ip=customer_ip,
                user_agent=user_agent
            )
            
            # Save customer message
            customer_message = ChatMessage(
                session_id=session.id,
                message=message,
                is_from_customer=True
            )
            self.db.add(customer_message)
            self.db.flush()  # Get message ID without committing
            
            # Generate AI response
            ai_response = await self.openai_service.generate_response(
                shop=shop,
                message=message,
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
            self.db.add(ai_message)
            
            # Commit all changes
            self.db.commit()
            
            logger.info(f"Chat processed for shop {shop.id}, session {session.session_id}")
            
            return ChatResponse(
                message=ai_response.message,
                session_id=session.session_id,
                suggestions=ai_response.suggestions,
                booking_prompt=ai_response.booking_prompt,
                services_mentioned=ai_response.services_mentioned
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Chat processing error for shop {shop.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process chat message"
            )
    
    async def get_chat_history(
        self,
        shop: Shop,
        session_id: str
    ) -> ChatHistoryResponse:
        """
        Get chat history for a session.
        
        Args:
            shop: Shop object
            session_id: Chat session ID
            
        Returns:
            ChatHistoryResponse with conversation history
            
        Raises:
            HTTPException: If session not found or access denied
        """
        try:
            # Get session
            session = self.db.query(ChatSession).filter(
                ChatSession.session_id == session_id,
                ChatSession.shop_id == shop.id
            ).first()
            
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Chat session not found"
                )
            
            # Get messages
            messages = self.db.query(ChatMessage).filter(
                ChatMessage.session_id == session.id
            ).order_by(ChatMessage.created_at).all()
            
            # Format messages
            history_messages = [
                ChatHistoryMessage(
                    message=msg.message,
                    is_from_customer=msg.is_from_customer,
                    timestamp=msg.created_at.isoformat() if msg.created_at else None
                )
                for msg in messages
            ]
            
            return ChatHistoryResponse(
                session_id=session_id,
                shop_name=shop.name,
                messages=history_messages
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve chat history"
            )
    
    async def get_chat_analytics(self, shop: Shop) -> Dict[str, Any]:
        """
        Get chat analytics for a shop.
        
        Args:
            shop: Shop object
            
        Returns:
            Dict with analytics data
        """
        try:
            # Get current month boundaries
            now = datetime.now()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_end = month_start + relativedelta(months=1)
            
            # Basic analytics queries
            total_sessions = self.db.query(ChatSession).filter(
                ChatSession.shop_id == shop.id
            ).count()
            
            total_messages = self.db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.shop_id == shop.id
            ).count()
            
            monthly_usage = self.db.query(ChatMessage).join(ChatSession).filter(
                ChatSession.shop_id == shop.id,
                ChatMessage.is_from_customer == True,
                ChatMessage.created_at >= month_start,
                ChatMessage.created_at < month_end
            ).count()
            
            # Calculate averages
            avg_messages_per_session = total_messages / total_sessions if total_sessions > 0 else 0
            
            return {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "monthly_usage": monthly_usage,
                "avg_messages_per_session": round(avg_messages_per_session, 2),
                "usage_limit": shop.plan.max_chats_per_month if shop.plan else 100,
                "usage_percentage": round((monthly_usage / (shop.plan.max_chats_per_month if shop.plan else 100)) * 100, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting chat analytics: {e}")
            return {
                "total_sessions": 0,
                "total_messages": 0,
                "monthly_usage": 0,
                "avg_messages_per_session": 0,
                "usage_limit": 0,
                "usage_percentage": 0
            }
    
    async def _is_usage_exceeded(self, shop: Shop) -> bool:
        """Check if shop has exceeded monthly chat usage"""
        if not shop.plan:
            return False  # No plan limits for shops without plans
        
        current_usage = self._get_monthly_chat_usage(shop.id)
        return current_usage >= shop.plan.max_chats_per_month
    
    async def _get_or_create_session(
        self,
        shop: Shop,
        session_id: Optional[str] = None,
        customer_ip: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ChatSession:
        """Get existing session or create new one"""
        
        # Generate session ID if not provided
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
        
        # Try to find existing session
        session = self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        
        if not session:
            # Create new session
            session = ChatSession(
                session_id=session_id,
                shop_id=shop.id,
                customer_ip=customer_ip or "unknown",
                customer_user_agent=user_agent or "unknown"
            )
            self.db.add(session)
            self.db.flush()  # Get session ID without committing
        
        return session
    
    def _get_monthly_chat_usage(self, shop_id: int) -> int:
        """Get current month's chat usage for a shop"""
        # Get current month boundaries
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = month_start + relativedelta(months=1)
        
        # Count chat messages from customers this month
        usage = self.db.query(ChatMessage).join(ChatSession).filter(
            ChatSession.shop_id == shop_id,
            ChatMessage.is_from_customer == True,
            ChatMessage.created_at >= month_start,
            ChatMessage.created_at < month_end
        ).count()
        
        return usage
    
    def _create_usage_exceeded_response(self, session_id: Optional[str]) -> ChatResponse:
        """Create response for when usage limit is exceeded"""
        return ChatResponse(
            message="This shop has reached its monthly chat limit. Please contact them directly for assistance.",
            session_id=session_id or f"session_{uuid.uuid4().hex[:8]}",
            suggestions=["Call the shop directly", "Visit their website", "Try again next month"],
            booking_prompt="Contact the shop to schedule your appointment!"
        )
    
    def create_fallback_response(self, session_id: Optional[str] = None) -> ChatResponse:
        """Create fallback response for errors"""
        return ChatResponse(
            message="I'm experiencing some technical difficulties right now. Please try again in a moment or contact the shop directly for immediate assistance.",
            session_id=session_id or f"session_{uuid.uuid4().hex[:8]}",
            suggestions=["Try again", "Contact shop directly", "Visit later"],
            booking_prompt="Call the shop to schedule your appointment!"
        )

# Factory function for dependency injection
def get_chat_service(db: Session) -> ChatService:
    """Factory function to create ChatService instance"""
    return ChatService(db)