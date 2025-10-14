"""
Health check router for monitoring application status.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    message: str
    version: str = "1.0.0"


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="Application is running properly"
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """Readiness check endpoint for Kubernetes."""
    # Add any dependency checks here (database, external services, etc.)
    return HealthResponse(
        status="ready",
        message="Application is ready to accept requests"
    )


@router.get("/live", response_model=HealthResponse)
async def liveness_check():
    """Liveness check endpoint for Kubernetes."""
    return HealthResponse(
        status="alive",
        message="Application is alive"
    )