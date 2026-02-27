"""
Configuration module for FinNexus backend.
Loads environment variables using pydantic BaseSettings.
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    google_api_key: str = ""  # Used for Gemini 2.5 Flash
    gemini_api_key: str = ""  # Alternative name for Gemini API
    newsapi_key: str = ""
    fred_api_key: str = ""
    
    # Paths
    chroma_persist_dir: str = "./chroma_db"
    model_cache_dir: str = "./models"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Logging
    log_level: str = "INFO"
    
    # App
    app_name: str = "FinNexus API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Render
    render_external_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()


def get_cors_origins() -> List[str]:
    """Get CORS origins, including Render URL if set."""
    origins = settings.cors_origins.copy()
    if settings.render_external_url:
        origins.append(settings.render_external_url)
    return origins
