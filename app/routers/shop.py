"""
Shop management router with endpoints for creating and managing auto detailing shops.
Handles shop CRUD operations, branding, API key management, and configuration.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.shop_service import ShopService, get_shop_service
from app.core.dependencies import (
    get_current_user,
    get_verified_user,
    get_user_shop,
    rate_limit_general,
    CurrentUser,
    VerifiedUser,
    UserShop
)
from app.models.shop import Shop
from app.schemas.shop import (
    ShopCreateRequest,
    ShopUpdateRequest,
    BookingSettingsRequest,
    ShopResponse,
    ShopListResponse,
    APIKeysResponse,
    MessageResponse
)
from app.core.security import SecurityHeaders


router = APIRouter()




def format_shop_response(shop: Shop) -> ShopResponse:
    """Format shop object for API response"""
    plan_info = None
    if shop.plan:
        plan_info = {
            "id": shop.plan.id,
            "name": shop.plan.name,
            "description": shop.plan.description,
            "max_chats_per_month": shop.plan.max_chats_per_month,
            "max_services": shop.plan.max_services,
            "features": shop.plan.features
        }
    
    return ShopResponse(
        id=shop.id,
        name=shop.name,
        address=shop.address,
        phone=shop.phone,
        logo_url=shop.logo_url,
        greeting_message=shop.greeting_message,
        primary_color=shop.primary_color,
        secondary_color=shop.secondary_color,
        subscription_status=shop.subscription_status,
        is_active=shop.is_active,
        created_at=shop.created_at.isoformat() if shop.created_at else None,
        updated_at=shop.updated_at.isoformat() if shop.updated_at else None,
        plan=plan_info
    )


@router.post(
    "/",
    response_model=ShopResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new shop",
    description="Create a new auto detailing shop for the authenticated user"
)
async def create_shop(
    shop_data: ShopCreateRequest,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Create a new shop for the authenticated user"""
    shop_service = get_shop_service(db)
    
    try:
        shop = await shop_service.create_shop(
            user=current_user,
            name=shop_data.name,
            address=shop_data.address,
            phone=shop_data.phone,
            logo_url=shop_data.logo_url,
            greeting_message=shop_data.greeting_message,
            primary_color=shop_data.primary_color,
            secondary_color=shop_data.secondary_color
        )
        
        return format_shop_response(shop)
        
    except HTTPException:
        raise
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Router error during shop creation: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create shop: {str(e)}"
        )


@router.get(
    "/",
    response_model=ShopListResponse,
    summary="Get user shops",
    description="Get all shops owned by the authenticated user"
)
async def get_user_shops(
    current_user: VerifiedUser,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Get all shops owned by the authenticated user"""
    shop_service = get_shop_service(db)
    
    try:
        shops = await shop_service.get_user_shops(current_user)
        
        shop_responses = [format_shop_response(shop) for shop in shops]
        
        return ShopListResponse(
            shops=shop_responses,
            total=len(shop_responses)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shops"
        )


@router.get(
    "/{shop_id}",
    response_model=ShopResponse,
    summary="Get shop details",
    description="Get detailed information about a specific shop"
)
async def get_shop(
    shop: UserShop,
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Get detailed information about a specific shop"""
    return format_shop_response(shop)


@router.put(
    "/{shop_id}",
    response_model=ShopResponse,
    summary="Update shop",
    description="Update shop information and settings"
)
async def update_shop(
    shop_data: ShopUpdateRequest,
    shop: UserShop,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Update shop information and settings"""
    shop_service = get_shop_service(db)
    
    try:
        updated_shop = await shop_service.update_shop(
            shop=shop,
            name=shop_data.name,
            address=shop_data.address,
            phone=shop_data.phone,
            logo_url=shop_data.logo_url,
            greeting_message=shop_data.greeting_message,
            primary_color=shop_data.primary_color,
            secondary_color=shop_data.secondary_color
        )
        
        return format_shop_response(updated_shop)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update shop"
        )


@router.delete(
    "/{shop_id}",
    response_model=MessageResponse,
    summary="Delete shop",
    description="Delete (deactivate) a shop"
)
async def delete_shop(
    shop: UserShop,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Delete (deactivate) a shop"""
    shop_service = get_shop_service(db)
    
    try:
        success = await shop_service.delete_shop(shop)
        
        if success:
            return MessageResponse(message="Shop deleted successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete shop"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete shop"
        )


@router.get(
    "/{shop_id}/api-keys",
    response_model=APIKeysResponse,
    summary="Get API keys",
    description="Get the shop's API keys for widget integration"
)
async def get_api_keys(
    shop: UserShop,
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Get shop's API keys for widget integration"""
    return APIKeysResponse(
        public_key=shop.public_api_key,
        private_key=shop.private_api_key
    )


@router.post(
    "/{shop_id}/api-keys/regenerate",
    response_model=APIKeysResponse,
    summary="Regenerate API keys",
    description="Generate new API keys for the shop (invalidates old keys)"
)
async def regenerate_api_keys(
    shop: UserShop,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Regenerate API keys for the shop"""
    shop_service = get_shop_service(db)
    
    try:
        new_keys = await shop_service.regenerate_api_keys(shop)
        
        return APIKeysResponse(
            public_key=new_keys["public_key"],
            private_key=new_keys["private_key"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate API keys"
        )


@router.put(
    "/{shop_id}/booking-settings",
    response_model=ShopResponse,
    summary="Update booking settings",
    description="Update calendar integration and booking rules"
)
async def update_booking_settings(
    booking_data: BookingSettingsRequest,
    shop: UserShop,
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Update calendar integration and booking settings"""
    shop_service = get_shop_service(db)
    
    try:
        updated_shop = await shop_service.update_booking_settings(
            shop=shop,
            calendar_type=booking_data.calendar_type,
            calendar_config=booking_data.calendar_config,
            booking_rules=booking_data.booking_rules
        )
        
        return format_shop_response(updated_shop)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update booking settings"
        )


@router.get(
    "/{shop_id}/widget-config",
    summary="Get widget configuration",
    description="Get configuration data for the chatbot widget"
)
async def get_widget_config(
    shop: UserShop,
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Get configuration data for the chatbot widget"""
    try:
        widget_config = {
            "shop_id": shop.id,
            "shop_name": shop.name,
            "greeting_message": shop.greeting_message,
            "primary_color": shop.primary_color,
            "secondary_color": shop.secondary_color,
            "logo_url": shop.logo_url,
            "public_api_key": shop.public_api_key,
            "is_active": shop.is_active and shop.subscription_status in ["trial", "active"]
        }
        
        return widget_config
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get widget configuration"
        )


# Note: Security headers would be added at the app level in main.py
# APIRouter doesn't support middleware, only the main FastAPI app does