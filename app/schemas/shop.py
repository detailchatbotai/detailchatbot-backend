"""
Shop-related Pydantic schemas for request/response validation.
Handles shop CRUD operations, branding, API key management, and configuration.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class ShopCreateRequest(BaseModel):
    """Shop creation request schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Shop name")
    address: str = Field(..., min_length=1, max_length=200, description="Shop address")
    phone: str = Field(..., min_length=1, max_length=20, description="Shop phone number")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    greeting_message: Optional[str] = Field(None, max_length=500, description="Custom greeting message")
    primary_color: Optional[str] = Field("#007bff", description="Primary brand color (hex)")
    secondary_color: Optional[str] = Field("#6c757d", description="Secondary brand color (hex)")
    
    @validator('primary_color', 'secondary_color')
    def validate_color(cls, v):
        """Validate hex color format"""
        if v and not v.startswith('#'):
            raise ValueError('Color must start with #')
        if v and len(v) not in [4, 7]:  # #RGB or #RRGGBB
            raise ValueError('Invalid color format')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Premium Auto Detailing",
                "address": "123 Main St, Anytown, ST 12345",
                "phone": "(555) 123-4567",
                "logo_url": "https://example.com/logo.png",
                "greeting_message": "Welcome! How can we help make your car shine?",
                "primary_color": "#007bff",
                "secondary_color": "#6c757d"
            }
        }


class ShopUpdateRequest(BaseModel):
    """Shop update request schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Shop name")
    address: Optional[str] = Field(None, min_length=1, max_length=200, description="Shop address")
    phone: Optional[str] = Field(None, min_length=1, max_length=20, description="Shop phone number")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    greeting_message: Optional[str] = Field(None, max_length=500, description="Custom greeting message")
    primary_color: Optional[str] = Field(None, description="Primary brand color (hex)")
    secondary_color: Optional[str] = Field(None, description="Secondary brand color (hex)")
    
    @validator('primary_color', 'secondary_color')
    def validate_color(cls, v):
        """Validate hex color format"""
        if v and not v.startswith('#'):
            raise ValueError('Color must start with #')
        if v and len(v) not in [4, 7]:  # #RGB or #RRGGBB
            raise ValueError('Invalid color format')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Premium Auto Detailing Plus",
                "greeting_message": "Welcome to our updated shop!",
                "primary_color": "#28a745"
            }
        }


class BookingSettingsRequest(BaseModel):
    """Booking settings update request schema"""
    calendar_type: Optional[str] = Field(None, description="Calendar integration type")
    calendar_config: Optional[Dict[str, Any]] = Field(None, description="Calendar configuration")
    booking_rules: Optional[Dict[str, Any]] = Field(None, description="Booking rules and constraints")
    
    @validator('calendar_type')
    def validate_calendar_type(cls, v):
        """Validate calendar type"""
        if v and v not in ["google", "calendly", "webhook"]:
            raise ValueError('Calendar type must be google, calendly, or webhook')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "calendar_type": "google",
                "calendar_config": {
                    "calendar_id": "primary",
                    "time_zone": "America/New_York"
                },
                "booking_rules": {
                    "advance_booking_hours": 24,
                    "buffer_minutes": 30,
                    "max_bookings_per_day": 8
                }
            }
        }


class ShopResponse(BaseModel):
    """Shop response schema"""
    id: int
    name: str
    address: str
    phone: str
    logo_url: Optional[str]
    greeting_message: str
    primary_color: str
    secondary_color: str
    subscription_status: str
    is_active: bool
    created_at: str
    updated_at: Optional[str]
    
    # Plan information
    plan: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Premium Auto Detailing",
                "address": "123 Main St, Anytown, ST 12345",
                "phone": "(555) 123-4567",
                "logo_url": "https://example.com/logo.png",
                "greeting_message": "Welcome! How can we help make your car shine?",
                "primary_color": "#007bff",
                "secondary_color": "#6c757d",
                "subscription_status": "trial",
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "plan": {
                    "name": "Trial",
                    "max_chats_per_month": 100,
                    "max_services": 5
                }
            }
        }


class ShopListResponse(BaseModel):
    """Shop list response schema"""
    shops: List[ShopResponse]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "shops": [
                    {
                        "id": 1,
                        "name": "Premium Auto Detailing",
                        "subscription_status": "trial",
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ],
                "total": 1
            }
        }


class APIKeysResponse(BaseModel):
    """API keys response schema"""
    public_key: str = Field(..., description="Public API key for widget")
    private_key: str = Field(..., description="Private API key for management")
    
    class Config:
        json_schema_extra = {
            "example": {
                "public_key": "dc_pub_1234567890abcdef",
                "private_key": "dc_pri_abcdef1234567890"
            }
        }


class MessageResponse(BaseModel):
    """Generic message response schema"""
    message: str = Field(..., description="Response message")