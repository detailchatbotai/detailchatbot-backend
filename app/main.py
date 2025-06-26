import logging
from fastapi import FastAPI
from app.api.v1.auth import router as auth_router
from app.api.v1.billing import router as billing_router
from app.api.v1.webhook import router as webhook_router
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models.user import Base
from app.core.database import engine

# Import other v1 routers as you add them, e.g. chatbot, booking, billing, etc.

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI(title="DetailChatBot API")

# Mount all v1 API routers under /api/v1
app.include_router(auth_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(webhook_router, prefix="/api/v1")
# Example: app.include_router(chatbot_router, prefix="/api/v1")

@app.get("/health")
async def health():
    """
    Simple health check endpoint.
    """
    return {"status": "OK"}

@app.on_event("startup")
async def on_startup():
    # Create all tables (development only)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
