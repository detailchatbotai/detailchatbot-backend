"""
Pydantic schemas for chat-related API endpoints.
Defines request and response models for chatbot interactions.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request schema for customer messages"""
    message: str = Field(..., min_length=1, max_length=1000, description="Customer message")
    session_id: Optional[str] = Field(None, description="Chat session ID (auto-generated if not provided)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hi, I'd like to know about your car detailing packages",
                "session_id": "session_123456"
            }
        }


class ChatResponse(BaseModel):
    """Chat response schema for AI-generated replies"""
    message: str = Field(..., description="AI-generated response message")
    session_id: str = Field(..., description="Chat session ID")
    suggestions: List[str] = Field(default=[], description="Suggested follow-up questions")
    booking_prompt: Optional[str] = Field(None, description="Prompt to encourage booking if applicable")
    services_mentioned: List[str] = Field(default=[], description="Services mentioned in the response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hi! Welcome to Premium Auto Detailing. We offer several packages including full service wash & wax, interior detailing, and ceramic coating. What type of service are you looking for?",
                "session_id": "session_123456",
                "suggestions": [
                    "Tell me about your full service package",
                    "What's included in interior detailing?",
                    "How much does ceramic coating cost?"
                ],
                "booking_prompt": None,
                "services_mentioned": ["Full Service Wash & Wax", "Interior Detailing", "Ceramic Coating"]
            }
        }


class ChatSessionResponse(BaseModel):
    """Chat session information schema"""
    session_id: str = Field(..., description="Unique session identifier")
    shop_id: int = Field(..., description="Shop ID this session belongs to")
    created_at: str = Field(..., description="Session creation timestamp")
    message_count: int = Field(..., description="Number of messages in this session")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_123456",
                "shop_id": 1,
                "created_at": "2024-01-01T12:00:00Z",
                "message_count": 5
            }
        }


class ChatHistoryRequest(BaseModel):
    """Request schema for retrieving chat history"""
    session_id: str = Field(..., description="Chat session ID")
    limit: Optional[int] = Field(50, ge=1, le=100, description="Maximum number of messages to return")
    offset: Optional[int] = Field(0, ge=0, description="Number of messages to skip")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_123456",
                "limit": 20,
                "offset": 0
            }
        }


class ChatMessageResponse(BaseModel):
    """Individual chat message schema"""
    id: int = Field(..., description="Message ID")
    message: str = Field(..., description="Message content")
    is_from_customer: bool = Field(..., description="True if message is from customer, False if from AI")
    created_at: str = Field(..., description="Message timestamp")
    tokens_used: Optional[int] = Field(None, description="OpenAI tokens used (for AI messages)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "message": "Hi, I'd like to know about your car detailing packages",
                "is_from_customer": True,
                "created_at": "2024-01-01T12:00:00Z",
                "tokens_used": None
            }
        }


class ChatHistoryMessage(BaseModel):
    """Simple chat message for history"""
    message: str = Field(..., description="Message content")
    is_from_customer: bool = Field(..., description="True if from customer")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class ChatHistoryResponse(BaseModel):
    """Chat history response schema"""
    session_id: str = Field(..., description="Chat session ID")
    shop_name: str = Field(..., description="Shop name")
    messages: List[ChatHistoryMessage] = Field(..., description="List of chat messages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_123456",
                "shop_name": "Premium Auto Detailing",
                "messages": [
                    {
                        "message": "Hi, I'd like to know about your packages",
                        "is_from_customer": True,
                        "timestamp": "2024-01-01T12:00:00Z"
                    },
                    {
                        "message": "We offer several packages...",
                        "is_from_customer": False,
                        "timestamp": "2024-01-01T12:00:30Z"
                    }
                ]
            }
        }


class ChatAnalyticsResponse(BaseModel):
    """Chat analytics response schema"""
    total_sessions: int = Field(..., description="Total number of chat sessions")
    total_messages: int = Field(..., description="Total number of messages")
    avg_messages_per_session: float = Field(..., description="Average messages per session")
    total_tokens_used: int = Field(..., description="Total OpenAI tokens used")
    most_common_topics: List[str] = Field(..., description="Most commonly discussed topics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_sessions": 150,
                "total_messages": 750,
                "avg_messages_per_session": 5.0,
                "total_tokens_used": 15000,
                "most_common_topics": [
                    "pricing",
                    "services",
                    "booking",
                    "ceramic coating",
                    "interior cleaning"
                ]
            }
        }