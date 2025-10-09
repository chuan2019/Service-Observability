"""
Configuration settings for the FastAPI application.
"""

import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    PROJECT_NAME: str = "FastAPI Prometheus Metrics"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Metrics
    METRICS_ENABLED: bool = True
    METRICS_PATH: str = "/metrics"
    
    # Database (for future use)
    DATABASE_URL: str = "sqlite:///./metrics.db"
    
    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()