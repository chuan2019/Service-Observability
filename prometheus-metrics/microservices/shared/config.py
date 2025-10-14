"""
Shared configuration settings for microservices.
"""

import os
from typing import List

from pydantic_settings import BaseSettings


class BaseServiceSettings(BaseSettings):
    """Base settings for all microservices."""
    
    # Environment
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
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@postgres:5432/ecommerce"
    
    # Service Discovery
    USER_SERVICE_URL: str = "http://user-service:8001"
    PRODUCT_SERVICE_URL: str = "http://product-service:8002"
    INVENTORY_SERVICE_URL: str = "http://inventory-service:8003"
    ORDER_SERVICE_URL: str = "http://order-service:8004"
    PAYMENT_SERVICE_URL: str = "http://payment-service:8005"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8006"
    
    model_config = {"env_file": ".env", "case_sensitive": True}


class UserServiceSettings(BaseServiceSettings):
    """User service specific settings."""
    SERVICE_NAME: str = "user-service"
    PORT: int = 8001


class ProductServiceSettings(BaseServiceSettings):
    """Product service specific settings."""
    SERVICE_NAME: str = "product-service"
    PORT: int = 8002


class InventoryServiceSettings(BaseServiceSettings):
    """Inventory service specific settings."""
    SERVICE_NAME: str = "inventory-service"
    PORT: int = 8003


class OrderServiceSettings(BaseServiceSettings):
    """Order service specific settings."""
    SERVICE_NAME: str = "order-service"
    PORT: int = 8004


class PaymentServiceSettings(BaseServiceSettings):
    """Payment service specific settings."""
    SERVICE_NAME: str = "payment-service"
    PORT: int = 8005


class NotificationServiceSettings(BaseServiceSettings):
    """Notification service specific settings."""
    SERVICE_NAME: str = "notification-service"
    PORT: int = 8006


class APIGatewaySettings(BaseServiceSettings):
    """API Gateway specific settings."""
    SERVICE_NAME: str = "api-gateway"
    PORT: int = 8000