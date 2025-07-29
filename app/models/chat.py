from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, nullable=False)
    customer_ip = Column(String, nullable=True)
    customer_user_agent = Column(String, nullable=True)

    # Booking outcome
    booking_made = Column(Boolean, default=False)
    booking_service_ids = Column(JSON, nullable=True)  # List of service IDs
    booking_total = Column(Float, nullable=True)

    # Metadata
    shop_id = Column(Integer, ForeignKey("shops.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    shop = relationship("Shop", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(Text, nullable=False)
    is_from_customer = Column(Boolean, nullable=False)

    # AI metadata
    openai_tokens_used = Column(Integer, nullable=True)
    openai_model = Column(String, nullable=True)

    # Metadata
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    session = relationship("ChatSession", back_populates="messages")