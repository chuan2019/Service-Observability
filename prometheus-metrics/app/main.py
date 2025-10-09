"""
FastAPI application with Prometheus metrics integration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.middleware.metrics import MetricsMiddleware
from app.routers import health, api, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Metrics endpoint: http://localhost:{settings.PORT}/metrics")
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
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(api.router, prefix="/api/v1", tags=["API"])
    app.include_router(tasks.router, prefix="/tasks", tags=["Tasks"])

    # Prometheus metrics endpoint - use custom registry
    from app.middleware.metrics import REGISTRY
    from fastapi import Response
    
    @app.get("/metrics")
    async def get_metrics():
        """Get Prometheus metrics."""
        from prometheus_client import generate_latest
        return Response(
            generate_latest(REGISTRY),
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )

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