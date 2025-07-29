"""
Authentication router with endpoints for user registration, login, and verification.
Implements secure authentication patterns with JWT tokens and email verification.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import AuthenticationService, get_auth_service
from app.core.dependencies import (
    get_current_user, 
    get_current_user_optional,
    verify_email_token,
    verify_magic_link_token,
    rate_limit_auth,
    rate_limit_general
)
from app.models.user import User
from app.core.security import SecurityHeaders
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    MagicLinkRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    AuthResponse,
    MessageResponse,
    UserProfileResponse
)


router = APIRouter()
security = HTTPBearer()




def format_user_response(user: User) -> dict:
    """Format user object for API response"""
    return {
        "id": user.id,
        "email": user.email,
        "is_verified": user.is_verified,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Register a new user account with email and optional password"
)
async def signup(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_auth)
):
    """Register a new user account"""
    auth_service = get_auth_service(db)
    
    try:
        user, access_token = await auth_service.register_user(
            email=user_data.email,
            password=user_data.password,
            send_verification=True
        )
        
        # Generate refresh token for password users
        refresh_token = None
        if user_data.password:
            from app.core.security import SecurityUtils
            refresh_token = SecurityUtils.create_refresh_token(
                data={"user_id": user.id, "email": user.email}
            )
        
        response_data = AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=format_user_response(user)
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="User login",
    description="Authenticate user with email and password"
)
async def login(
    credentials: UserLoginRequest,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_auth)
):
    """Authenticate user with email and password"""
    auth_service = get_auth_service(db)
    
    try:
        user, access_token, refresh_token = await auth_service.authenticate_user(
            email=credentials.email,
            password=credentials.password
        )
        
        response_data = AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=format_user_response(user)
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post(
    "/magic-link",
    response_model=MessageResponse,
    summary="Send magic link",
    description="Send passwordless authentication link to user's email"
)
async def send_magic_link(
    request: MagicLinkRequest,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_auth)
):
    """Send magic link for passwordless authentication"""
    auth_service = get_auth_service(db)
    
    try:
        success = await auth_service.send_magic_link(request.email)
        
        if success:
            return MessageResponse(
                message="Magic link sent to your email address"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send magic link"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send magic link"
        )


@router.get(
    "/magic-link",
    response_model=AuthResponse,
    summary="Verify magic link",
    description="Verify magic link token and authenticate user"
)
async def verify_magic_link(
    token: str = Query(..., description="Magic link token"),
    db: Session = Depends(get_db)
):
    """Verify magic link token and authenticate user"""
    auth_service = get_auth_service(db)
    
    try:
        user, access_token, refresh_token = await auth_service.verify_magic_link(token)
        
        response_data = AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=format_user_response(user)
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired magic link"
        )


@router.get(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email address",
    description="Verify user's email address using verification token"
)
async def verify_email(
    token: str = Query(..., description="Email verification token"),
    db: Session = Depends(get_db)
):
    """Verify user email address"""
    auth_service = get_auth_service(db)
    
    try:
        verified_user = await auth_service.verify_email(token)
        
        return MessageResponse(
            message="Email verified successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification failed"
        )


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend email verification",
    description="Resend email verification link to current user"
)
async def resend_verification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_auth)
):
    """Resend email verification for current user"""
    auth_service = get_auth_service(db)
    
    try:
        success = await auth_service.resend_verification_email(current_user)
        
        if success:
            return MessageResponse(
                message="Verification email sent"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Refresh access token",
    description="Refresh access token using refresh token"
)
async def refresh_tokens(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Refresh access token using refresh token"""
    auth_service = get_auth_service(db)
    
    try:
        new_access_token, new_refresh_token = await auth_service.refresh_token(
            request.refresh_token
        )
        
        # Get user info from the new token for response
        from app.core.security import SecurityUtils
        token_data = SecurityUtils.verify_token(new_access_token, "access")
        user = db.query(User).filter(User.id == token_data.user_id).first()
        
        response_data = AuthResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            user=format_user_response(user)
        )
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token refresh failed"
        )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user",
    description="Get current authenticated user's profile information"
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Get current user's profile information"""
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        is_verified=current_user.is_verified,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change current user's password"
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_auth)
):
    """Change current user's password"""
    auth_service = get_auth_service(db)
    
    try:
        success = await auth_service.change_password(
            user=current_user,
            current_password=request.current_password,
            new_password=request.new_password
        )
        
        if success:
            return MessageResponse(
                message="Password changed successfully"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Logout current user (client should discard tokens)"
)
async def logout(
    current_user: User = Depends(get_current_user_optional),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """
    Logout user. Since we're using stateless JWT tokens,
    the client should discard the tokens.
    In a production system, you might want to implement token blacklisting.
    """
    return MessageResponse(
        message="Logged out successfully"
    )


# Note: Security headers would be added at the app level in main.py
# APIRouter doesn't support middleware, only the main FastAPI app does