from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    shop_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    plan = Column(String, nullable=False)
    is_subscribed = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    supabase_user_id = Column(String, nullable=False)
    ai_query_usage = Column(Integer, default=0)
    ai_usage_reset = Column(DateTime(timezone=True), nullable=True)
    is_verified = Column(Boolean, default=False)

    # Relationships
    shops = relationship("Shop", back_populates="owner")