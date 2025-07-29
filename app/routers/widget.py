"""
Widget router for generating embeddable chatbot widgets.
Provides clean API endpoints for JavaScript widget generation.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.shop import Shop
from app.services.widget_service import WidgetService
from app.core.dependencies import rate_limit_general

logger = logging.getLogger(__name__)
router = APIRouter()


def get_widget_service(db: Session = Depends(get_db)) -> WidgetService:
    """Dependency to provide WidgetService instance"""
    return WidgetService(db)


@router.get(
    "/{shop_api_key}/embed.js",
    response_class=PlainTextResponse,
    summary="Get embeddable widget JavaScript",
    description="Get JavaScript code to embed the chatbot widget on shop's website"
)
async def get_widget_javascript(
    shop_api_key: str,
    theme: Optional[str] = "light",
    position: Optional[str] = "bottom-right",
    db: Session = Depends(get_db),
    widget_service: WidgetService = Depends(get_widget_service),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Generate JavaScript widget code for embedding"""
    
    try:
        # Verify shop exists and is active
        shop = db.query(Shop).filter(
            Shop.public_api_key == shop_api_key,
            Shop.is_active == True
        ).first()
        
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found or inactive"
            )
        
        # Validate parameters
        if theme not in ["light", "dark"]:
            theme = "light"
        if position not in ["bottom-right", "bottom-left"]:
            position = "bottom-right"
        
        # Generate widget JavaScript using service
        widget_js = widget_service.generate_widget_javascript(
            shop=shop,
            theme=theme,
            position=position
        )
        
        # Set proper content type and caching headers
        response = Response(
            content=widget_js,
            media_type="application/javascript",
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Content-Security-Policy": "default-src 'self'",
            }
        )
        
        logger.info(f"Widget JavaScript generated for shop {shop.id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating widget for {shop_api_key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate widget"
        )


@router.get(
    "/{shop_api_key}/config",
    summary="Get widget configuration",
    description="Get widget configuration and customization options for a shop"
)
async def get_widget_config(
    shop_api_key: str,
    db: Session = Depends(get_db),
    widget_service: WidgetService = Depends(get_widget_service),
    _rate_limit: bool = Depends(rate_limit_general)
):
    """Get widget configuration for a shop"""
    
    try:
        # Verify shop exists and is active
        shop = db.query(Shop).filter(
            Shop.public_api_key == shop_api_key,
            Shop.is_active == True
        ).first()
        
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found or inactive"
            )
        
        # Get widget configuration using service
        config = widget_service.get_widget_config(shop)
        
        logger.info(f"Widget config retrieved for shop {shop.id}")
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting widget config for {shop_api_key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve widget configuration"
        )