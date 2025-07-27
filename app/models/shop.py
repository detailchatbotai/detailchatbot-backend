from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    logo_url = Column(String, nullable=True)

    # Branding
    greeting_message = Column(Text, default="Hi! How can I help you with your auto detailing needs?")
    primary_color = Column(String, default="#007bff")
    secondary_color = Column(String, default="#6c757d")

    # Booking integration
    calendar_type = Column(String, nullable=True)  # 'google', 'calendly', 'webhook'
    calendar_config = Column(JSON, nullable=True)  # OAuth tokens, webhook URLs, etc.

    # Business hours and rules
    booking_rules = Column(JSON, nullable=True)  # hours, lead time, buffer, etc.

    # Subscription
    stripe_customer_id = Column(String, nullable=True)
    subscription_status = Column(String, default="trial")  # trial, active, cancelled
    plan_id = Column(Integer, ForeignKey("plans.id"))

    # API keys
    public_api_key = Column(String, unique=True, nullable=False)
    private_api_key = Column(String, unique=True, nullable=False)

    # Metadata
    owner_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="shops")
    services = relationship("Service", back_populates="shop")
    plan = relationship("Plan", back_populates="shops")
    chat_sessions = relationship("ChatSession", back_populates="shop")