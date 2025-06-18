# app/models/booking.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.core.database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id         = Column(Integer, primary_key=True, index=True, autoincrement=True)
    shop_id    = Column(String, ForeignKey("shops.id"), nullable=False)
    customer_email = Column(String, nullable=False)
    timestamp  = Column(DateTime(timezone=True), server_default=func.now())
