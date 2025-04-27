import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///agentX.db")
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-for-jwt-tokens")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email settings
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "noreply@agentx.com")
    
    # Frontend URL for password reset links
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8000")
    
    # API settings
    API_PREFIX: str = "/api/v1"
    APP_NAME: str = "AgentX - Multi-Model Agentic RAG System"
    APP_DESCRIPTION: str = "An advanced system for managing Agent, Pinecone and FAISS integrations, Text and PDF processing."
    APP_VERSION: str = "1.0.0"
    
    # File storage
    MEDIA_DIR: str = "media"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


@lru_cache()
def get_settings():
    return Settings()

# Ensure media directory exists
os.makedirs(get_settings().MEDIA_DIR, exist_ok=True) 