"""
Service-related Pydantic schemas for request/response validation
"""

from typing import Optional, List
from pydantic import BaseModel, Field, validator


class ServiceCreateRequest(BaseModel):
    """Service creation request schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Service name")
    description: Optional[str] = Field(None, max_length=1000, description="Service description")
    price: float = Field(..., ge=0, description="Service price in dollars")
    duration_minutes: int = Field(..., ge=1, le=1440, description="Service duration in minutes (1-1440)")
    is_active: bool = Field(True, description="Whether service is active")
    is_addon: bool = Field(False, description="Whether service is an add-on")
    
    @validator('price')
    def validate_price(cls, v):
        """Validate price is reasonable"""
        if v > 10000:
            raise ValueError('Price cannot exceed $10,000')
        return round(v, 2)  # Round to 2 decimal places
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Premium Detail Package",
                "description": "Complete interior and exterior detailing with paint protection",
                "price": 149.99,
                "duration_minutes": 180,
                "is_active": True,
                "is_addon": False
            }
        }


class ServiceUpdateRequest(BaseModel):
    """Service update request schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Service name")
    description: Optional[str] = Field(None, max_length=1000, description="Service description")
    price: Optional[float] = Field(None, ge=0, description="Service price in dollars")
    duration_minutes: Optional[int] = Field(None, ge=1, le=1440, description="Service duration in minutes")
    is_active: Optional[bool] = Field(None, description="Whether service is active")
    is_addon: Optional[bool] = Field(None, description="Whether service is an add-on")
    
    @validator('price')
    def validate_price(cls, v):
        """Validate price is reasonable"""
        if v is not None:
            if v > 10000:
                raise ValueError('Price cannot exceed $10,000')
            return round(v, 2)
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Premium Detail Package - Updated",
                "price": 159.99,
                "is_active": True
            }
        }


class ServiceResponse(BaseModel):
    """Service response schema"""
    id: int
    name: str
    description: Optional[str]
    price: float
    duration_minutes: int
    is_active: bool
    is_addon: bool
    shop_id: int
    created_at: str
    updated_at: Optional[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Premium Detail Package",
                "description": "Complete interior and exterior detailing with paint protection",
                "price": 149.99,
                "duration_minutes": 180,
                "is_active": True,
                "is_addon": False,
                "shop_id": 1,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class ServiceListResponse(BaseModel):
    """Service list response schema"""
    services: List[ServiceResponse]
    total: int
    active_count: int
    addon_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "services": [
                    {
                        "id": 1,
                        "name": "Basic Wash",
                        "price": 25.00,
                        "duration_minutes": 30,
                        "is_active": True,
                        "is_addon": False
                    }
                ],
                "total": 5,
                "active_count": 4,
                "addon_count": 2
            }
        }


class MessageResponse(BaseModel):
    """Generic message response schema"""
    message: str = Field(..., description="Response message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Service created successfully"
            }
        }