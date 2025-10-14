"""
FastAPI application with Prometheus metrics integration and microservices architecture.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.middleware.metrics import MetricsMiddleware
from app.database import init_db
from app.routers import (
    health, users, products, orders, payments,
    inventory, demo, metrics
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Metrics endpoint: http://localhost:{settings.PORT}/metrics")
    
    # Initialize database
    print("Initializing database...")
    await init_db()
    print("Database initialized successfully")
    
    yield
    # Shutdown
    print("Shutting down...")


def create_app() -> FastAPI:
    """Create FastAPI application with all configurations."""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="FastAPI application with Prometheus metrics integration",
        version=settings.VERSION,
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom metrics middleware
    app.add_middleware(MetricsMiddleware)

    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(metrics.router, tags=["Metrics"])
    
    # Include microservices routers
    app.include_router(users.router, prefix="/api/v1", tags=["Users"])
    app.include_router(products.router, prefix="/api/v1", tags=["Products"])
    app.include_router(orders.router, prefix="/api/v1", tags=["Orders"])
    app.include_router(payments.router, prefix="/api/v1", tags=["Payments"])
    app.include_router(inventory.router, prefix="/api/v1", tags=["Inventory"])
    app.include_router(demo.router, prefix="/api/v1", tags=["Demo"])

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )