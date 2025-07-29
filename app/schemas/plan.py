"""
Pydantic schemas for plan and subscription operations.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator


class SubscriptionRequest(BaseModel):
    """Subscription creation request schema"""
    plan_id: int = Field(..., description="Plan ID to subscribe to")
    billing_cycle: str = Field("monthly", description="Billing cycle: monthly or yearly")
    success_url: Optional[str] = Field(None, description="Custom success URL")
    cancel_url: Optional[str] = Field(None, description="Custom cancel URL")
    
    @validator('billing_cycle')
    def validate_billing_cycle(cls, v):
        """Validate billing cycle"""
        if v not in ["monthly", "yearly"]:
            raise ValueError('Billing cycle must be monthly or yearly')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": 2,
                "billing_cycle": "monthly",
                "success_url": "https://myshop.com/success",
                "cancel_url": "https://myshop.com/cancel"
            }
        }


class PlanResponse(BaseModel):
    """Plan response schema"""
    id: int
    name: str
    description: Optional[str]
    price_monthly: float
    price_yearly: float
    max_chats_per_month: int
    max_services: int
    features: List[str]
    is_active: bool
    
    # Computed fields
    yearly_savings: Optional[float] = None
    popular: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 2,
                "name": "Pro",
                "description": "Perfect for growing detailing shops",
                "price_monthly": 29.99,
                "price_yearly": 299.99,
                "max_chats_per_month": 1000,
                "max_services": 25,
                "features": [
                    "AI Chatbot",
                    "Advanced Analytics",
                    "Calendar Integration",
                    "Custom Branding",
                    "Priority Support"
                ],
                "is_active": True,
                "yearly_savings": 59.88,
                "popular": True
            }
        }


class PlansListResponse(BaseModel):
    """Plans list response schema"""
    plans: List[PlanResponse]
    current_plan: Optional[PlanResponse] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "plans": [
                    {
                        "id": 1,
                        "name": "Trial",
                        "price_monthly": 0.0,
                        "popular": False
                    },
                    {
                        "id": 2,
                        "name": "Pro",
                        "price_monthly": 29.99,
                        "popular": True
                    }
                ],
                "current_plan": {
                    "id": 1,
                    "name": "Trial"
                }
            }
        }


class CheckoutResponse(BaseModel):
    """Checkout session response schema"""
    checkout_session_id: str = Field(..., description="Stripe checkout session ID")
    checkout_url: str = Field(..., description="URL to redirect user for payment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "checkout_session_id": "cs_1234567890",
                "checkout_url": "https://checkout.stripe.com/c/pay/cs_1234567890"
            }
        }


class SubscriptionResponse(BaseModel):
    """Current subscription response schema"""
    subscription_id: Optional[str] = None
    status: str
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    cancel_at_period_end: bool = False
    plan: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "subscription_id": "sub_1234567890",
                "status": "active",
                "current_period_start": "2024-01-01T00:00:00Z",
                "current_period_end": "2024-02-01T00:00:00Z",
                "cancel_at_period_end": False,
                "plan": {
                    "id": 2,
                    "name": "Pro",
                    "price": 29.99,
                    "currency": "usd",
                    "interval": "month"
                }
            }
        }


class UsageResponse(BaseModel):
    """Usage statistics response schema"""
    current_period_start: str
    current_period_end: str
    chats_used: int
    chats_limit: int
    services_used: int
    services_limit: int
    usage_percentage: Dict[str, float]
    
    class Config:
        json_schema_extra = {
            "example": {
                "current_period_start": "2024-01-01T00:00:00Z",
                "current_period_end": "2024-02-01T00:00:00Z",
                "chats_used": 250,
                "chats_limit": 1000,
                "services_used": 8,
                "services_limit": 25,
                "usage_percentage": {
                    "chats": 25.0,
                    "services": 32.0
                }
            }
        }


class BillingPortalResponse(BaseModel):
    """Billing portal response schema"""
    portal_url: str = Field(..., description="URL to Stripe customer portal")
    
    class Config:
        json_schema_extra = {
            "example": {
                "portal_url": "https://billing.stripe.com/p/session_1234567890"
            }
        }


class MessageResponse(BaseModel):
    """Generic message response schema"""
    message: str = Field(..., description="Response message")