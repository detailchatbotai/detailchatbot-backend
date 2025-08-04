from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    # Database - REQUIRED environment variable for production
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/detailchatbot_dev"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Convert asyncpg URLs to psycopg2 URLs
        if self.DATABASE_URL.startswith("postgresql+asyncpg://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        elif "postgresql" in self.DATABASE_URL and "+asyncpg" not in self.DATABASE_URL and "+psycopg2" not in self.DATABASE_URL:
            # Ensure we're using psycopg2
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")

    # Auth & Security - REQUIRED environment variable for production  
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Generate secure key for development only
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Password Security
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100  # requests per minute
    RATE_LIMIT_WINDOW: int = 60     # seconds
    LOGIN_RATE_LIMIT: int = 5       # login attempts per minute
    
    # Session Security
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
    
    # API Security
    API_KEY_LENGTH: int = 32
    API_KEY_PREFIX: str = "dc_"  # detailchatbot prefix
    
    # External APIs
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # Email Security
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    
    # Email Verification
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    MAGIC_LINK_EXPIRE_MINUTES: int = 15
    
    # Frontend URLs
    FRONTEND_URL: str = "http://localhost:3000"  # For email links

    # CORS Security
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Local dev
        "http://localhost:8080",  # Local dev
        "http://127.0.0.1:3000",  # Local dev
        "http://127.0.0.1:8080",  # Local dev
        "https://detailchatbot-frontend.onrender.com",  # DEV frontend
        "https://detailchatbot.ai",  # Production frontend
        "https://app.detailchatbot.ai",  # Production app
        "https://www.detailchatbot.ai",  # Production www
        "null"  # For widget file:// testing
    ]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    ALLOWED_HEADERS: List[str] = ["*"]

    # App settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Security Headers
    ENABLE_SECURITY_HEADERS: bool = True
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"
    
    def validate_production_config(self) -> None:
        """Validate that all required environment variables are set for production"""
        if not self.is_production:
            return
            
        required_vars = {
            "DATABASE_URL": self.DATABASE_URL,
            "SECRET_KEY": self.SECRET_KEY, 
            "OPENAI_API_KEY": self.OPENAI_API_KEY,
            "STRIPE_SECRET_KEY": self.STRIPE_SECRET_KEY,
            "STRIPE_WEBHOOK_SECRET": self.STRIPE_WEBHOOK_SECRET,
        }
        
        missing_vars = []
        for var_name, var_value in required_vars.items():
            if not var_value or var_value == "":
                missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables for production: {', '.join(missing_vars)}"
            )

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra environment variables


settings = Settings()

# Validate production configuration on startup
if settings.is_production:
    settings.validate_production_config()