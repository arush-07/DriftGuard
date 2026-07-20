import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./driftguard.db"
    SECRET_KEY: str = "super-driftguard-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 600  # Longer expire for easy demo
    ML_SERVICE_URL: str = "http://127.0.0.1:8080"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
