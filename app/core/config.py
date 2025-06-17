from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    # OPENAI_API_KEY: str
    SENDGRID_API_KEY: str
    SENDGRID_SENDER: str
    # STRIPE_SECRET_KEY: str
    # CALENDLY_API_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
