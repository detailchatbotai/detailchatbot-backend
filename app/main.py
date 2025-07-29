from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.openapi.utils import get_openapi
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.routers import auth, shop, service, plan, chat, webhooks, widget
from app.core.security import SecurityHeaders

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

# Custom OpenAPI schema with security definitions
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="DetailChatbot.ai API",
        version="1.0.0",
        description="Backend service for AI chatbot for auto-detailing shops",
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT access token"
        }
    }
    
    # Define which endpoints require authentication
    protected_endpoints = [
        "/api/v1/auth/me",
        "/api/v1/auth/resend-verification", 
        "/api/v1/auth/change-password",
        "/api/v1/auth/logout",
        "/api/v1/shops",
        "/api/v1/services", 
        "/api/v1/plans",
        "/api/v1/chat",
    ]
    
    # Apply security to protected endpoints
    for route_path, route_methods in openapi_schema["paths"].items():
        # Check if this path or any parent path requires authentication
        requires_auth = any(route_path.startswith(endpoint) for endpoint in protected_endpoints)
        
        if requires_auth:
            for method, route_info in route_methods.items():
                route_info["security"] = [{"HTTPBearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

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
app.include_router(shop.router, prefix="/api/v1/shops", tags=["shops"])
app.include_router(service.router, prefix="/api/v1/services", tags=["services"])
app.include_router(plan.router, prefix="/api/v1/plans", tags=["plans"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(widget.router, prefix="/api/v1/widget", tags=["widget"])
app.include_router(webhooks.router, prefix="/api/v1/webhooks", tags=["webhooks"])

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Add security headers
    headers = SecurityHeaders.get_security_headers()
    for key, value in headers.items():
        response.headers[key] = value
    
    return response

@app.get("/")
async def root():
    return {"message": "DetailChatbot.ai API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}