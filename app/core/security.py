"""
Security utilities for authentication, password hashing, JWT tokens, and API keys.
Implements security best practices for a production SaaS application.
"""

import secrets
import string
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.config import settings


class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass


class TokenData(BaseModel):
    """Token payload data structure"""
    user_id: Optional[int] = None
    email: Optional[str] = None
    token_type: str = "access"  # access, refresh, email_verification, magic_link


class PasswordValidator:
    """Validates password strength according to security requirements"""
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, list[str]]:
        """
        Validate password against security requirements.
        
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if settings.PASSWORD_REQUIRE_NUMBERS and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common weak patterns
        if password.lower() in ['password', '123456', 'qwerty', 'admin']:
            errors.append("Password is too common and easily guessable")
        
        return len(errors) == 0, errors


class SecurityUtils:
    """Core security utilities for the application"""
    
    # Password hashing context
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        # Validate password strength first
        is_valid, errors = PasswordValidator.validate_password(password)
        if not is_valid:
            raise SecurityError(f"Password validation failed: {'; '.join(errors)}")
        
        return cls.pwd_context.hash(password)
    
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Stored password hash
            
        Returns:
            True if password matches, False otherwise
        """
        try:
            return cls.pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False
    
    @classmethod
    def create_access_token(
        cls, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Token payload data
            expires_delta: Custom expiration time
            
        Returns:
            JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        })
        
        try:
            encoded_jwt = jwt.encode(
                to_encode, 
                settings.SECRET_KEY, 
                algorithm=settings.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            raise SecurityError(f"Failed to create access token: {str(e)}")
    
    @classmethod
    def create_refresh_token(cls, data: Dict[str, Any]) -> str:
        """
        Create a JWT refresh token with longer expiration.
        
        Args:
            data: Token payload data
            
        Returns:
            JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        })
        
        try:
            encoded_jwt = jwt.encode(
                to_encode, 
                settings.SECRET_KEY, 
                algorithm=settings.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            raise SecurityError(f"Failed to create refresh token: {str(e)}")
    
    @classmethod
    def create_email_verification_token(cls, email: str) -> str:
        """
        Create a token for email verification.
        
        Args:
            email: User email address
            
        Returns:
            JWT verification token
        """
        data = {"email": email, "type": "email_verification"}
        expire = datetime.now(timezone.utc) + timedelta(
            hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS
        )
        
        to_encode = data.copy()
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        })
        
        try:
            return jwt.encode(
                to_encode, 
                settings.SECRET_KEY, 
                algorithm=settings.ALGORITHM
            )
        except Exception as e:
            raise SecurityError(f"Failed to create verification token: {str(e)}")
    
    @classmethod
    def create_magic_link_token(cls, email: str) -> str:
        """
        Create a token for magic link authentication.
        
        Args:
            email: User email address
            
        Returns:
            JWT magic link token
        """
        data = {"email": email, "type": "magic_link"}
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.MAGIC_LINK_EXPIRE_MINUTES
        )
        
        to_encode = data.copy()
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        })
        
        try:
            return jwt.encode(
                to_encode, 
                settings.SECRET_KEY, 
                algorithm=settings.ALGORITHM
            )
        except Exception as e:
            raise SecurityError(f"Failed to create magic link token: {str(e)}")
    
    @classmethod
    def verify_token(cls, token: str, expected_type: str = "access") -> TokenData:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string
            expected_type: Expected token type for validation
            
        Returns:
            TokenData object with decoded payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            
            # Verify token type
            token_type = payload.get("type")
            if token_type != expected_type:
                raise credentials_exception
            
            # Extract user data based on token type
            if expected_type in ["access", "refresh"]:
                user_id: int = payload.get("user_id")
                email: str = payload.get("email")
                if user_id is None:
                    raise credentials_exception
                return TokenData(user_id=user_id, email=email, token_type=token_type)
            
            elif expected_type in ["email_verification", "magic_link"]:
                email: str = payload.get("email")
                if email is None:
                    raise credentials_exception
                return TokenData(email=email, token_type=token_type)
            
            else:
                raise credentials_exception
                
        except JWTError:
            raise credentials_exception
        except Exception:
            raise credentials_exception


class APIKeyGenerator:
    """Generate secure API keys for shops"""
    
    @staticmethod
    def generate_api_key(key_type: str = "public") -> str:
        """
        Generate a secure API key.
        
        Args:
            key_type: Type of key - 'public' or 'private'
            
        Returns:
            Generated API key string
        """
        # Generate cryptographically secure random key
        key_length = settings.API_KEY_LENGTH
        
        # Use URL-safe characters for API keys
        alphabet = string.ascii_letters + string.digits + "-_"
        key_body = ''.join(secrets.choice(alphabet) for _ in range(key_length))
        
        # Add prefix to identify key type and source
        prefix = f"{settings.API_KEY_PREFIX}{key_type[:3]}_"
        
        return f"{prefix}{key_body}"
    
    @staticmethod
    def generate_shop_keys() -> Dict[str, str]:
        """
        Generate both public and private API keys for a shop.
        
        Returns:
            Dictionary with 'public' and 'private' keys
        """
        return {
            "public": APIKeyGenerator.generate_api_key("public"),
            "private": APIKeyGenerator.generate_api_key("private")
        }


class SecurityHeaders:
    """Security headers for HTTP responses"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """
        Get recommended security headers for HTTP responses.
        
        Returns:
            Dictionary of security headers
        """
        if not settings.ENABLE_SECURITY_HEADERS:
            return {}
        
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        if settings.is_production:
            headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self'"
            )
        
        return headers


# Utility functions for common security operations
def generate_secure_filename(original_filename: str) -> str:
    """Generate a secure filename to prevent directory traversal attacks"""
    # Remove path components and dangerous characters
    safe_chars = string.ascii_letters + string.digits + ".-_"
    filename = "".join(c for c in original_filename if c in safe_chars)
    
    # Add timestamp to ensure uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
    
    return f"{timestamp}_{name}.{ext}" if ext else f"{timestamp}_{name}"


def sanitize_input(input_string: str, max_length: int = 1000) -> str:
    """Basic input sanitization to prevent common attacks"""
    if not input_string:
        return ""
    
    # Truncate to max length
    sanitized = input_string[:max_length]
    
    # Remove null bytes and other control characters
    sanitized = "".join(char for char in sanitized if ord(char) >= 32 or char in ['\n', '\r', '\t'])
    
    return sanitized.strip()


# Export main classes and functions
__all__ = [
    "SecurityUtils",
    "PasswordValidator", 
    "APIKeyGenerator",
    "SecurityHeaders",
    "TokenData",
    "SecurityError",
    "generate_secure_filename",
    "sanitize_input"
]