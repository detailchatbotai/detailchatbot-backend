from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.models.user import Base

class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    services = Column(Text, nullable=True)  # JSON or comma-separated for MVP
    pricing = Column(Text, nullable=True)   # JSON or comma-separated for MVP
    hours = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    owner = relationship("User", back_populates="shops")

