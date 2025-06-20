import os
import logging
import ssl
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

class Base(DeclarativeBase):
    pass

ssl_ctx = ssl.create_default_context()

url = os.getenv("ASYNC_DATABASE_URL")
logging.warning("ASYNC_DATABASE_URL SEEN BY APP → %r", url)
logging.warning("HOST PART → %s", urlparse(url).hostname)

engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"ssl": ssl_ctx},
    echo=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()
