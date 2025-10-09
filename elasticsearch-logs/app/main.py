"""Main FastAPI application entry point."""

import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.routers import health, orders, users

# Setup logging before creating the app
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(
        "Starting FastAPI application",
        extra={
            "event": "app_startup",
            "environment": settings.ENVIRONMENT,
            "log_level": settings.LOG_LEVEL,
        },
    )
    yield
    logger.info("Shutting down FastAPI application", extra={"event": "app_shutdown"})


# Create FastAPI app
app = FastAPI(
    title="FastAPI Elasticsearch Logging Demo",
    description="A sample FastAPI application with Elasticsearch logging integration",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all HTTP requests with detailed information."""
    request_id = str(uuid.uuid4())
    start_time = datetime.utcnow()

    # Log incoming request
    logger.info(
        "Incoming request",
        extra={
            "event": "request_start",
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "timestamp": start_time.isoformat(),
        },
    )

    # Process request
    try:
        response = await call_next(request)

        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds()

        # Log response
        logger.info(
            "Request completed",
            extra={
                "event": "request_end",
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "duration_seconds": duration,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return response

    except Exception as exc:
        duration = (datetime.utcnow() - start_time).total_seconds()

        # Log error
        logger.error(
            "Request failed",
            extra={
                "event": "request_error",
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "error": str(exc),
                "error_type": type(exc).__name__,
                "duration_seconds": duration,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        raise exc


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with proper logging."""
    logger.warning(
        "HTTP exception occurred",
        extra={
            "event": "http_exception",
            "status_code": exc.status_code,
            "detail": exc.detail,
            "method": request.method,
            "url": str(request.url),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with proper logging."""
    logger.error(
        "Unhandled exception occurred",
        extra={
            "event": "unhandled_exception",
            "error": str(exc),
            "error_type": type(exc).__name__,
            "method": request.method,
            "url": str(request.url),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])


@app.get("/")
async def root():
    """Root endpoint."""
    logger.info(
        "Root endpoint accessed",
        extra={"event": "root_access", "timestamp": datetime.utcnow().isoformat()},
    )
    return {
        "message": "FastAPI Elasticsearch Logging Demo",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
