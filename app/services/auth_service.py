"""
Authentication service layer for user registration, login, and email verification.
Handles business logic for user authentication operations.
"""

import logging
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.user import User
from app.core.security import SecurityUtils, SecurityError, PasswordValidator
from app.utils.email import EmailService
from app.core.config import settings


logger = logging.getLogger(__name__)


class AuthenticationService:
    """Service class for handling user authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
    
    async def register_user(
        self, 
        email: str, 
        password: Optional[str] = None,
        send_verification: bool = True
    ) -> Tuple[User, str]:
        """
        Register a new user with email and optional password.
        
        Args:
            email: User email address
            password: User password (optional for magic link users)
            send_verification: Whether to send email verification
            
        Returns:
            Tuple of (User object, access_token)
            
        Raises:
            HTTPException: If registration fails
        """
        # Normalize email
        email = email.lower().strip()
        
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Validate email format
        if not self._is_valid_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Hash password if provided
        hashed_password = None
        if password:
            try:
                hashed_password = SecurityUtils.hash_password(password)
            except SecurityError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
        # Create user
        try:
            import uuid
            user = User(
                email=email,
                hashed_password=hashed_password or "",
                shop_name="",  # Will be set up later
                is_active=True,
                is_verified=False,  # Email verification required
                plan="free",
                is_subscribed=False,
                supabase_user_id=str(uuid.uuid4())
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User registered successfully: {email}")
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Database error during user registration: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User registration failed"
            )
        
        # Send email verification if requested
        if send_verification:
            try:
                await self._send_verification_email(user)
            except Exception as e:
                logger.warning(f"Failed to send verification email to {email}: {e}")
                # Don't fail registration if email sending fails
        
        # Generate access token
        access_token = SecurityUtils.create_access_token(
            data={"user_id": user.id, "email": user.email}
        )
        
        return user, access_token
    
    async def authenticate_user(self, email: str, password: str) -> Tuple[User, str, str]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: User password
            
        Returns:
            Tuple of (User, access_token, refresh_token)
            
        Raises:
            HTTPException: If authentication fails
        """
        # Normalize email
        email = email.lower().strip()
        
        # Find user
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            # Prevent user enumeration by taking same time as password verification
            SecurityUtils.verify_password("dummy", "$2b$12$dummy.hash")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        # Verify password
        if not user.hashed_password or not SecurityUtils.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Generate tokens
        token_data = {"user_id": user.id, "email": user.email}
        access_token = SecurityUtils.create_access_token(data=token_data)
        refresh_token = SecurityUtils.create_refresh_token(data=token_data)
        
        # Update last login (if you have this field)
        try:
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to update last login for user {user.id}: {e}")
        
        logger.info(f"User authenticated successfully: {email}")
        return user, access_token, refresh_token
    
    async def send_magic_link(self, email: str) -> bool:
        """
        Send magic link for passwordless authentication.
        
        Args:
            email: User email address
            
        Returns:
            True if email was sent successfully
        """
        # Normalize email
        email = email.lower().strip()
        
        # Check if user exists (create if not)
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            # Auto-register user for magic link auth
            user, _ = await self.register_user(email, password=None, send_verification=False)
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        # Generate magic link token
        try:
            magic_token = SecurityUtils.create_magic_link_token(email)
            
            # Send magic link email
            magic_link = f"{settings.frontend_url}/auth/magic-link?token={magic_token}"
            await self.email_service.send_magic_link_email(email, magic_link)
            
            logger.info(f"Magic link sent to: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send magic link to {email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send magic link"
            )
    
    async def verify_magic_link(self, token: str) -> Tuple[User, str, str]:
        """
        Verify magic link token and authenticate user.
        
        Args:
            token: Magic link token
            
        Returns:
            Tuple of (User, access_token, refresh_token)
        """
        try:
            token_data = SecurityUtils.verify_token(token, "magic_link")
            
            user = self.db.query(User).filter(User.email == token_data.email).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is disabled"
                )
            
            # Auto-verify email for magic link users
            if not user.is_verified:
                user.is_verified = True
                self.db.commit()
            
            # Generate tokens
            token_data = {"user_id": user.id, "email": user.email}
            access_token = SecurityUtils.create_access_token(data=token_data)
            refresh_token = SecurityUtils.create_refresh_token(data=token_data)
            
            logger.info(f"User authenticated via magic link: {user.email}")
            return user, access_token, refresh_token
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Magic link verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired magic link"
            )
    
    async def verify_email(self, token: str) -> User:
        """
        Verify user email with verification token.
        
        Args:
            token: Email verification token
            
        Returns:
            Verified user object
        """
        try:
            token_data = SecurityUtils.verify_token(token, "email_verification")
            
            user = self.db.query(User).filter(User.email == token_data.email).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if user.is_verified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already verified"
                )
            
            # Mark as verified
            user.is_verified = True
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info(f"Email verified for user: {user.email}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Email verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
    
    async def resend_verification_email(self, user: User) -> bool:
        """
        Resend email verification for a user.
        
        Args:
            user: User object
            
        Returns:
            True if email was sent successfully
        """
        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        try:
            await self._send_verification_email(user)
            logger.info(f"Verification email resent to: {user.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to resend verification email to {user.email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
    
    async def refresh_token(self, refresh_token: str) -> Tuple[str, str]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
        """
        try:
            token_data = SecurityUtils.verify_token(refresh_token, "refresh")
            
            # Verify user still exists and is active
            user = self.db.query(User).filter(User.id == token_data.user_id).first()
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
            
            # Generate new tokens
            new_token_data = {"user_id": user.id, "email": user.email}
            new_access_token = SecurityUtils.create_access_token(data=new_token_data)
            new_refresh_token = SecurityUtils.create_refresh_token(data=new_token_data)
            
            return new_access_token, new_refresh_token
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    
    async def change_password(
        self, 
        user: User, 
        current_password: str, 
        new_password: str
    ) -> bool:
        """
        Change user password.
        
        Args:
            user: User object
            current_password: Current password
            new_password: New password
            
        Returns:
            True if password was changed successfully
        """
        # Verify current password
        if not user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password change not allowed for magic link users"
            )
        
        if not SecurityUtils.verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        try:
            new_hashed_password = SecurityUtils.hash_password(new_password)
        except SecurityError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Update password
        try:
            user.hashed_password = new_hashed_password
            user.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            
            logger.info(f"Password changed for user: {user.email}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to change password for user {user.id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    async def _send_verification_email(self, user: User) -> None:
        """Send email verification email to user"""
        verification_token = SecurityUtils.create_email_verification_token(user.email)
        verification_link = f"{settings.frontend_url}/auth/verify-email?token={verification_token}"
        
        await self.email_service.send_verification_email(
            user.email, 
            verification_link
        )
    
    async def delete_user_account(self, user_id: int) -> bool:
        """
        Delete user account and all associated data.
        This will cascade delete shops, services, chat sessions, etc.
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            True if successful
            
        Raises:
            HTTPException: If deletion fails
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Delete user (will cascade delete shops, services, etc. via foreign key constraints)
            self.db.delete(user)
            self.db.commit()
            
            logger.info(f"User account deleted: {user.email} (ID: {user_id})")
            return True
            
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete user account {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete account"
            )


# Factory function for dependency injection
def get_auth_service(db: Session) -> AuthenticationService:
    """Factory function to create AuthenticationService instance"""
    return AuthenticationService(db)