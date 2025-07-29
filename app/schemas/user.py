"""
User-related Pydantic schemas for request/response validation
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """User registration request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: Optional[str] = Field(None, min_length=8, description="User password (optional for magic link)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!"
            }
        }


class UserLoginRequest(BaseModel):
    """User login request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!"
            }
        }


class MagicLinkRequest(BaseModel):
    """Magic link request schema"""
    email: EmailStr = Field(..., description="User email address")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class RefreshTokenRequest(BaseModel):
    """Token refresh request schema"""
    refresh_token: str = Field(..., description="Valid refresh token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class ChangePasswordRequest(BaseModel):
    """Password change request schema"""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_password": "OldPassword123!",
                "new_password": "NewSecurePassword456!"
            }
        }


class AuthResponse(BaseModel):
    """Authentication response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: dict = Field(..., description="User information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "email": "user@example.com",
                    "is_verified": True,
                    "created_at": "2024-01-01T00:00:00Z"
                }
            }
        }


class UserProfileResponse(BaseModel):
    """User profile response schema"""
    id: int
    email: str
    is_verified: bool
    is_active: bool
    created_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "is_verified": True,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }


class MessageResponse(BaseModel):
    """Generic message response schema"""
    message: str = Field(..., description="Response message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation completed successfully"
            }
        }