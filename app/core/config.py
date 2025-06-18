# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # OpenAI
    OPENAI_API_KEY: str

    # SendGrid
    SENDGRID_API_KEY: str
    SENDGRID_SENDER: str

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_PRICE_STARTER: str
    SUCCESS_URL: str
    CANCEL_URL: str
    STRIPE_WEBHOOK_SECRET: str

    # Calendly
    CALENDLY_API_KEY: str
    CALENDLY_SIGNING_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
