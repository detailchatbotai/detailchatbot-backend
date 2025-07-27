from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import logging
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.routers import auth, shops, services, plans, chat, analytics, webhooks

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting DetailChatbot.ai API")
    yield
    # Shutdown
    logger.info("Shutting down DetailChatbot.ai API")

app = FastAPI(
    title="DetailChatbot.ai API",
    description="Backend service for AI chatbot for auto-detailing shops",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(shops.router, prefix="/api/v1/shops", tags=["shops"])
app.include_router(services.router, prefix="/api/v1/services", tags=["services"])
app.include_router(plans.router, prefix="/api/v1/plans", tags=["plans"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])

@app.get("/")
async def root():
    return {"message": "DetailChatbot.ai API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}