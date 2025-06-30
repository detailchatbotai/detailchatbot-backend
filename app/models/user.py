from sqlalchemy import Column, String, Integer, DateTime, Boolean, func, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        UniqueConstraint("shop_name", name="uq_shop_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    shop_name = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Stripe integration fields
    stripe_customer_id = Column(String(100), nullable=True, index=True)
    stripe_subscription_id = Column(String(100), nullable=True, index=True)
    plan = Column(String(50), default="starter", nullable=False)  # starter, pro, elite
    is_subscribed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    supabase_user_id = Column(String(50), unique=True, nullable=False, index=True)
    ai_query_usage = Column(Integer, default=0, nullable=False)
    ai_usage_reset = Column(DateTime(timezone=True), nullable=True)

    shops = relationship("Shop", back_populates="owner", cascade="all, delete-orphan")
