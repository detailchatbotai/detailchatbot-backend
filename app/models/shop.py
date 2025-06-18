from sqlalchemy import Column, String, JSON
from app.core.database import Base  # import the shared Base

class Shop(Base):
    __tablename__ = "shops"

    id           = Column(String, primary_key=True, index=True)
    name         = Column(String, nullable=False)
    services     = Column(JSON,   nullable=False)
    booking_link = Column(String, nullable=False)
