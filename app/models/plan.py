from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Basic, Pro, Elite
    description = Column(String, nullable=True)
    price_monthly = Column(Float, nullable=False)
    price_yearly = Column(Float, nullable=False)

    # Limits
    max_chats_per_month = Column(Integer, nullable=False)
    max_services = Column(Integer, nullable=False)
    features = Column(JSON, nullable=True)  # List of features

    # Stripe
    stripe_price_id_monthly = Column(String, nullable=True)
    stripe_price_id_yearly = Column(String, nullable=True)

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    shops = relationship("Shop", back_populates="plan")