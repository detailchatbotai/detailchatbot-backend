from sqlalchemy import Column, String, JSON, Boolean
from app.core.database import Base    # <-- shared declarative_base()

class Shop(Base):
    __tablename__ = "shops"

    id           = Column(String, primary_key=True, index=True)
    name         = Column(String, nullable=False)
    services     = Column(JSON,   nullable=False)   # e.g. {"Exterior":100,"Interior":150}
    booking_link = Column(String, nullable=False)   # e.g. Calendly URL

    is_active    = Column(Boolean, default=False, nullable=False)
    plan_tier    = Column(String,  default="starter", nullable=False)
