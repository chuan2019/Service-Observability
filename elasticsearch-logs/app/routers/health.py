"""Health check endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str
    version: str


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    logger.info(
        "Health check accessed",
        extra={
            "event": "health_check",
            "endpoint": "/health",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    return HealthResponse(
        status="healthy", timestamp=datetime.utcnow().isoformat(), version="1.0.0"
    )


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with service status."""
    logger.info(
        "Detailed health check accessed",
        extra={
            "event": "detailed_health_check",
            "endpoint": "/health/detailed",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    # You can add more detailed checks here
    # For example, database connectivity, external service health, etc.

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "api": "healthy",
            "elasticsearch": "healthy",  # You can add actual checks
            "database": "healthy",
        },
        "uptime": "unknown",  # You can track actual uptime
    }
