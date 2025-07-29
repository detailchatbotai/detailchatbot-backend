
"""
Database configuration and session management for the DetailChatbot.ai application.
Uses SQLAlchemy with PostgreSQL for production and SQLite for development.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings


# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    # SQLAlchemy 2.0 style
    echo=settings.DEBUG,  # Log SQL statements in debug mode
    pool_pre_ping=True,   # Verify connections before use
    pool_recycle=300      # Recycle connections every 5 minutes
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create declarative base for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI.
    Creates a new database session for each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)