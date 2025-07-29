"""
FastAPI dependencies for authentication, authorization, and security.
Provides reusable dependency functions for route protection and user injection.
"""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Header, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.models.user import User
from app.models.shop import Shop
from app.core.security import SecurityUtils, TokenData
from app.core.config import settings


# Security scheme for JWT bearer tokens
security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Custom authentication error"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Custom authorization error"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user from JWT token (optional - returns None if no token).
    Used for endpoints that work with or without authentication.
    """
    if not credentials:
        return None
    
    try:
        token_data = SecurityUtils.verify_token(credentials.credentials, "access")
        user = db.query(User).filter(User.id == token_data.user_id).first()
        
        if not user or not user.is_active:
            return None
        
        return user
    except Exception:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from JWT token (required).
    Raises 401 if no valid token provided.
    """
    if not credentials:
        raise AuthenticationError("Missing authentication token")
    
    try:
        token_data = SecurityUtils.verify_token(credentials.credentials, "access")
        user = db.query(User).filter(User.id == token_data.user_id).first()
        
        if not user:
            raise AuthenticationError("User not found")
        
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise AuthenticationError("Invalid authentication token")


async def get_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and ensure they are email verified.
    """
    if not current_user.is_verified:
        raise AuthorizationError("Email verification required")
    
    return current_user


async def get_user_shop(
    shop_id: int,
    current_user: User = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Shop:
    """
    Get a shop and verify the current user owns it.
    """
    shop = db.query(Shop).filter(
        and_(
            Shop.id == shop_id,
            Shop.owner_id == current_user.id,
            Shop.is_active == True
        )
    ).first()
    
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop not found or access denied"
        )
    
    return shop


async def get_shop_by_api_key(
    api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> Shop:
    """
    Get shop by API key for widget/public endpoints.
    Validates public API key format and shop status.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Validate API key format
    if not api_key.startswith(settings.API_KEY_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )
    
    # Find shop by public API key
    shop = db.query(Shop).filter(
        and_(
            Shop.public_api_key == api_key,
            Shop.is_active == True
        )
    ).first()
    
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Check subscription status
    if shop.subscription_status not in ["trial", "active"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Subscription required"
        )
    
    return shop


async def get_shop_with_private_key(
    api_key: str = Header(..., alias="X-Private-API-Key"),
    db: Session = Depends(get_db)
) -> Shop:
    """
    Get shop by private API key for admin/management endpoints.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Private API key required"
        )
    
    # Validate API key format
    if not api_key.startswith(settings.API_KEY_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )
    
    # Find shop by private API key
    shop = db.query(Shop).filter(
        and_(
            Shop.private_api_key == api_key,
            Shop.is_active == True
        )
    ).first()
    
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid private API key"
        )
    
    return shop


async def verify_email_token(
    token: str = Query(..., description="Email verification token"),
    db: Session = Depends(get_db)
) -> User:
    """
    Verify email verification token and return user.
    """
    try:
        token_data = SecurityUtils.verify_token(token, "email_verification")
        user = db.query(User).filter(User.email == token_data.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )


async def verify_magic_link_token(
    token: str = Query(..., description="Magic link token"),
    db: Session = Depends(get_db)
) -> User:
    """
    Verify magic link token and return user.
    """
    try:
        token_data = SecurityUtils.verify_token(token, "magic_link")
        user = db.query(User).filter(User.email == token_data.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled"
            )
        
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired magic link"
        )


async def check_subscription_limits(
    shop: Shop = Depends(get_user_shop),
    db: Session = Depends(get_db)
) -> Shop:
    """
    Check if shop has exceeded subscription limits.
    Can be used as a dependency for endpoints that consume quota.
    """
    # This would typically check against usage analytics
    # For now, just ensure subscription is active
    if shop.subscription_status not in ["trial", "active"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    # TODO: Add actual usage limit checking against plan limits
    # This would query the analytics/usage tables and compare with plan limits
    
    return shop


# Rate limiting dependency (basic implementation)
class RateLimiter:
    """Basic rate limiting implementation"""
    
    def __init__(self, requests: int = 100, window: int = 60):
        self.requests = requests
        self.window = window
        # In production, use Redis or similar for distributed rate limiting
        self._requests = {}
    
    async def __call__(
        self, 
        request_id: str = Header(None, alias="X-Forwarded-For")
    ):
        """Rate limiting dependency"""
        # For now, just return - implement proper rate limiting with Redis/etc
        # This is a placeholder for production rate limiting
        return True


# Create instances for common use cases
rate_limit_general = RateLimiter(
    requests=settings.RATE_LIMIT_REQUESTS,
    window=settings.RATE_LIMIT_WINDOW
)

rate_limit_auth = RateLimiter(
    requests=settings.LOGIN_RATE_LIMIT,
    window=60
)


# Type annotations for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[Optional[User], Depends(get_current_user_optional)]
VerifiedUser = Annotated[User, Depends(get_verified_user)]
UserShop = Annotated[Shop, Depends(get_user_shop)]
ShopByAPIKey = Annotated[Shop, Depends(get_shop_by_api_key)]
ShopByPrivateKey = Annotated[Shop, Depends(get_shop_with_private_key)]


# Export for use in routers
__all__ = [
    "get_current_user",
    "get_current_user_optional", 
    "get_verified_user",
    "get_user_shop",
    "get_shop_by_api_key",
    "get_shop_with_private_key",
    "verify_email_token",
    "verify_magic_link_token",
    "check_subscription_limits",
    "rate_limit_general",
    "rate_limit_auth",
    "CurrentUser",
    "CurrentUserOptional",
    "VerifiedUser", 
    "UserShop",
    "ShopByAPIKey",
    "ShopByPrivateKey",
    "AuthenticationError",
    "AuthorizationError"
]