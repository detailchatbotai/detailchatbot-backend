"""
Shop service layer for managing auto detailing shop operations.
Handles business logic for shop creation, management, and configuration.
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_
from fastapi import HTTPException, status

from app.models.shop import Shop
from app.models.user import User
from app.models.service import Service
from app.models.plan import Plan
from app.core.security import APIKeyGenerator, sanitize_input
from app.utils.email import EmailService
from app.core.config import settings


logger = logging.getLogger(__name__)


class ShopService:
    """Service class for handling shop operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
    
    async def create_shop(
        self,
        user: User,
        name: str,
        address: str,
        phone: str,
        logo_url: Optional[str] = None,
        greeting_message: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None
    ) -> Shop:
        """
        Create a new shop for a user.
        
        Args:
            user: Shop owner
            name: Shop name
            address: Shop address
            phone: Shop phone number
            logo_url: Optional logo URL
            greeting_message: Custom greeting message
            primary_color: Primary brand color
            secondary_color: Secondary brand color
            
        Returns:
            Created shop object
            
        Raises:
            HTTPException: If shop creation fails
        """
        # Check if user already has a shop (for MVP, limit to one shop per user)
        existing_shop = self.db.query(Shop).filter(
            and_(Shop.owner_id == user.id, Shop.is_active == True)
        ).first()
        
        if existing_shop:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active shop. Multiple shops not supported in current plan."
            )
        
        # Validate and sanitize inputs
        name = sanitize_input(name.strip(), max_length=100)
        address = sanitize_input(address.strip(), max_length=200)
        phone = sanitize_input(phone.strip(), max_length=20)
        
        if not name or not address or not phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Shop name, address, and phone are required"
            )
        
        # Validate phone format (basic validation)
        if not self._is_valid_phone(phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format"
            )
        
        # Set defaults for optional fields
        if not greeting_message:
            greeting_message = f"Hi! Welcome to {name}. How can I help you with your auto detailing needs?"
        
        greeting_message = sanitize_input(greeting_message, max_length=500)
        
        # Validate colors if provided
        if primary_color and not self._is_valid_color(primary_color):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid primary color format. Use hex format (#RRGGBB)"
            )
        
        if secondary_color and not self._is_valid_color(secondary_color):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid secondary color format. Use hex format (#RRGGBB)"
            )
        
        # Generate API keys
        try:
            api_keys = APIKeyGenerator.generate_shop_keys()
        except Exception as e:
            logger.error(f"Failed to generate API keys: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate shop credentials"
            )
        
        # Get default plan (trial) or create one
        default_plan = self.db.query(Plan).filter(Plan.name == "Trial").first()
        if not default_plan:
            logger.info("No Trial plan found, creating default trial plan")
            try:
                default_plan = await self._create_default_trial_plan()
            except Exception as e:
                logger.error(f"Failed to create trial plan: {e}")
                # For now, allow shop creation without a plan
                default_plan = None
        
        # Create shop
        try:
            shop = Shop(
                name=name,
                address=address,
                phone=phone,
                logo_url=logo_url,
                greeting_message=greeting_message,
                primary_color=primary_color or "#007bff",
                secondary_color=secondary_color or "#6c757d",
                public_api_key=api_keys["public"],
                private_api_key=api_keys["private"],
                owner_id=user.id,
                plan_id=default_plan.id if default_plan else None,
                subscription_status="trial",
                is_active=True
            )
            
            self.db.add(shop)
            self.db.commit()
            self.db.refresh(shop)
            
            logger.info(f"Shop created successfully: {name} (ID: {shop.id}) for user {user.id}")
            
            # Send welcome email
            try:
                await self.email_service.send_welcome_email(user.email, name)
            except Exception as e:
                logger.warning(f"Failed to send welcome email: {e}")
                # Don't fail shop creation if email fails
            
            return shop
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database error during shop creation: {e}")
            
            # Check for specific constraint violations
            if "public_api_key" in str(e):
                # Retry with new API keys (very unlikely collision)
                logger.warning("API key collision detected, retrying...")
                return await self.create_shop(
                    user, name, address, phone, logo_url, 
                    greeting_message, primary_color, secondary_color
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Shop creation failed. Please check your input."
                )
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error during shop creation: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Shop creation failed: {str(e)}"
            )
    
    async def get_user_shops(self, user: User) -> List[Shop]:
        """
        Get all shops owned by a user.
        
        Args:
            user: Shop owner
            
        Returns:
            List of user's shops
        """
        shops = self.db.query(Shop).filter(
            and_(Shop.owner_id == user.id, Shop.is_active == True)
        ).all()
        
        return shops
    
    async def get_shop_by_id(self, shop_id: int, user: User) -> Shop:
        """
        Get a specific shop by ID, ensuring user owns it.
        
        Args:
            shop_id: Shop ID
            user: Shop owner
            
        Returns:
            Shop object
            
        Raises:
            HTTPException: If shop not found or access denied
        """
        shop = self.db.query(Shop).filter(
            and_(
                Shop.id == shop_id,
                Shop.owner_id == user.id,
                Shop.is_active == True
            )
        ).first()
        
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found or access denied"
            )
        
        return shop
    
    async def update_shop(
        self,
        shop: Shop,
        name: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        logo_url: Optional[str] = None,
        greeting_message: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None
    ) -> Shop:
        """
        Update shop information.
        
        Args:
            shop: Shop to update
            name: New shop name
            address: New shop address
            phone: New shop phone
            logo_url: New logo URL
            greeting_message: New greeting message
            primary_color: New primary color
            secondary_color: New secondary color
            
        Returns:
            Updated shop object
        """
        try:
            # Update fields if provided
            if name is not None:
                name = sanitize_input(name.strip(), max_length=100)
                if not name:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Shop name cannot be empty"
                    )
                shop.name = name
            
            if address is not None:
                address = sanitize_input(address.strip(), max_length=200)
                if not address:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Shop address cannot be empty"
                    )
                shop.address = address
            
            if phone is not None:
                phone = sanitize_input(phone.strip(), max_length=20)
                if not phone or not self._is_valid_phone(phone):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid phone number"
                    )
                shop.phone = phone
            
            if logo_url is not None:
                shop.logo_url = logo_url
            
            if greeting_message is not None:
                greeting_message = sanitize_input(greeting_message.strip(), max_length=500)
                shop.greeting_message = greeting_message
            
            if primary_color is not None:
                if not self._is_valid_color(primary_color):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid primary color format"
                    )
                shop.primary_color = primary_color
            
            if secondary_color is not None:
                if not self._is_valid_color(secondary_color):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid secondary color format"
                    )
                shop.secondary_color = secondary_color
            
            shop.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(shop)
            
            logger.info(f"Shop updated successfully: {shop.id}")
            return shop
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update shop {shop.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update shop"
            )
    
    async def regenerate_api_keys(self, shop: Shop) -> Dict[str, str]:
        """
        Regenerate API keys for a shop.
        
        Args:
            shop: Shop to regenerate keys for
            
        Returns:
            Dict with new public and private keys
        """
        try:
            # Generate new API keys
            new_keys = APIKeyGenerator.generate_shop_keys()
            
            # Update shop with new keys
            shop.public_api_key = new_keys["public"]
            shop.private_api_key = new_keys["private"]
            shop.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"API keys regenerated for shop {shop.id}")
            
            return {
                "public_key": new_keys["public"],
                "private_key": new_keys["private"]
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to regenerate API keys for shop {shop.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to regenerate API keys"
            )
    
    async def delete_shop(self, shop: Shop) -> bool:
        """
        Soft delete a shop (mark as inactive).
        
        Args:
            shop: Shop to delete
            
        Returns:
            True if deletion successful
        """
        try:
            shop.is_active = False
            shop.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info(f"Shop soft deleted: {shop.id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete shop {shop.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete shop"
            )
    
    async def get_shop_by_api_key(self, api_key: str) -> Optional[Shop]:
        """
        Get shop by API key (for widget access).
        
        Args:
            api_key: Public API key
            
        Returns:
            Shop object if found, None otherwise
        """
        shop = self.db.query(Shop).filter(
            and_(
                Shop.public_api_key == api_key,
                Shop.is_active == True
            )
        ).first()
        
        return shop
    
    async def update_booking_settings(
        self,
        shop: Shop,
        calendar_type: Optional[str] = None,
        calendar_config: Optional[Dict[str, Any]] = None,
        booking_rules: Optional[Dict[str, Any]] = None
    ) -> Shop:
        """
        Update shop booking integration settings.
        
        Args:
            shop: Shop to update
            calendar_type: Type of calendar integration
            calendar_config: Calendar configuration
            booking_rules: Booking rules and constraints
            
        Returns:
            Updated shop object
        """
        try:
            if calendar_type is not None:
                if calendar_type not in ["google", "calendly", "webhook", None]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid calendar type"
                    )
                shop.calendar_type = calendar_type
            
            if calendar_config is not None:
                shop.calendar_config = calendar_config
            
            if booking_rules is not None:
                shop.booking_rules = booking_rules
            
            shop.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(shop)
            
            logger.info(f"Booking settings updated for shop {shop.id}")
            return shop
            
        except HTTPException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update booking settings for shop {shop.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update booking settings"
            )
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        import re
        # Basic phone validation - adjust regex as needed
        pattern = r'^[\+]?[1-9][\d]{0,15}$|^[\(]?[\d]{3}[\)]?[\s\-]?[\d]{3}[\s\-]?[\d]{4}$'
        return re.match(pattern, phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")) is not None
    
    def _is_valid_color(self, color: str) -> bool:
        """Validate hex color format"""
        import re
        pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
        return re.match(pattern, color) is not None
    
    async def _create_default_trial_plan(self) -> Plan:
        """Create default trial plan if it doesn't exist"""
        try:
            trial_plan = Plan(
                name="Trial",
                description="Free trial plan with basic features",
                price_monthly=0.0,
                price_yearly=0.0,
                max_chats_per_month=100,
                max_services=5,
                features=[
                    "AI Chatbot",
                    "Basic Analytics",
                    "Email Support"
                ],
                is_active=True
            )
            
            self.db.add(trial_plan)
            self.db.commit()
            self.db.refresh(trial_plan)
            
            logger.info("Default trial plan created")
            return trial_plan
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create default trial plan: {e}")
            raise


# Factory function for dependency injection
def get_shop_service(db: Session) -> ShopService:
    """Factory function to create ShopService instance"""
    return ShopService(db)