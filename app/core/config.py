from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    ENVIRONMENT: str = Field("dev", env="ENVIRONMENT")
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_KEY: str = Field(..., env="SUPABASE_KEY")
    SUPABASE_JWT_SECRET: str = Field(..., env="SUPABASE_JWT_SECRET")
    STRIPE_SECRET_KEY: str = Field(..., env="STRIPE_SECRET_KEY")
    STRIPE_PRICE_STARTER: str = Field(..., env="STRIPE_PRICE_STARTER")
    # Add additional Stripe price IDs as needed:
    # STRIPE_PRICE_PRO: str = Field(..., env="STRIPE_PRICE_PRO")
    # STRIPE_PRICE_ELITE: str = Field(..., env="STRIPE_PRICE_ELITE")
    SUCCESS_URL: str = Field(..., env="SUCCESS_URL")
    CANCEL_URL: str = Field(..., env="CANCEL_URL")
    STRIPE_WEBHOOK_SECRET: str = Field(..., env="STRIPE_WEBHOOK_SECRET")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()