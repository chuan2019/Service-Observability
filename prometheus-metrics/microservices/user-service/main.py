"""User microservice main application."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge, REGISTRY
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import httpx

from shared.config import UserServiceSettings
from shared.database import init_db_manager, get_db_manager
from shared.schemas import UserCreate, UserUpdate, UserResponse, HealthResponse


# Metrics
USER_OPERATIONS = Counter(
    'user_service_operations_total',
    'Total user service operations',
    ['operation', 'status'],
    registry=REGISTRY
)

USER_OPERATION_DURATION = Histogram(
    'user_service_operation_duration_seconds',
    'User service operation duration',
    ['operation'],
    registry=REGISTRY
)

ACTIVE_USERS = Gauge(
    'user_service_active_users',
    'Number of active users',
    registry=REGISTRY
)

settings = UserServiceSettings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Starting {settings.SERVICE_NAME}")
    print(f"Environment: {settings.ENVIRONMENT}")
    
    # Initialize database
    init_db_manager(settings.DATABASE_URL)
    db_manager = get_db_manager()
    await db_manager.init_db()
    print("Database initialized successfully")
    
    yield
    
    # Shutdown
    db_manager = get_db_manager()
    if db_manager:
        await db_manager.close()
    print("Shutting down...")


app = FastAPI(
    title="User Service",
    description="User management microservice",
    version="1.0.0",
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

# Prometheus metrics endpoint
metrics_app = make_asgi_app(registry=REGISTRY)
app.mount("/metrics", metrics_app)


async def get_session():
    """Get database session."""
    db_manager = get_db_manager()
    async for session in db_manager.get_session():
        yield session


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        timestamp=datetime.utcnow()
    )


@app.get("/health/services")
async def check_all_services():
    """Check health of all microservices."""
    
    service_urls = {
        "user": os.getenv("USER_SERVICE_URL", "http://user-service:8001"),
        "product": os.getenv("PRODUCT_SERVICE_URL", "http://product-service:8002"),
        "inventory": os.getenv("INVENTORY_SERVICE_URL", "http://inventory-service:8003"),
        "order": os.getenv("ORDER_SERVICE_URL", "http://order-service:8004"),
        "payment": os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8005"),
        "notification": os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8006")
    }
    
    service_status = {}
    
    async with httpx.AsyncClient() as client:
        for service_name, service_url in service_urls.items():
            try:
                response = await client.get(f"{service_url}/health", timeout=5.0)
                service_status[service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": service_url,
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None
                }
            except Exception as e:
                service_status[service_name] = {
                    "status": "unhealthy",
                    "url": service_url,
                    "error": str(e)
                }
    
    return {
        "gateway_status": "healthy",
        "services": service_status
    }


@app.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new user."""
    with USER_OPERATION_DURATION.labels(operation="create").time():
        try:
            # Import here to avoid circular imports
            from shared.models import User
            
            # Check if user already exists
            existing_user = await session.execute(
                select(User).where(User.email == user_data.email)
            )
            if existing_user.scalar_one_or_none():
                USER_OPERATIONS.labels(operation="create", status="error").inc()
                raise HTTPException(status_code=400, detail="User already exists")
            
            # Create new user
            user = User(**user_data.model_dump())
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            USER_OPERATIONS.labels(operation="create", status="success").inc()
            ACTIVE_USERS.inc()
            
            return UserResponse.model_validate(user)
            
        except Exception as e:
            USER_OPERATIONS.labels(operation="create", status="error").inc()
            await session.rollback()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
):
    """Get all users."""
    with USER_OPERATION_DURATION.labels(operation="list").time():
        try:
            from shared.models import User
            
            result = await session.execute(
                select(User).offset(skip).limit(limit)
            )
            users = result.scalars().all()
            
            USER_OPERATIONS.labels(operation="list", status="success").inc()
            return [UserResponse.model_validate(user) for user in users]
            
        except Exception as e:
            USER_OPERATIONS.labels(operation="list", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific user."""
    with USER_OPERATION_DURATION.labels(operation="get").time():
        try:
            from shared.models import User
            
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                USER_OPERATIONS.labels(operation="get", status="error").inc()
                raise HTTPException(status_code=404, detail="User not found")
            
            USER_OPERATIONS.labels(operation="get", status="success").inc()
            return UserResponse.model_validate(user)
            
        except HTTPException:
            raise
        except Exception as e:
            USER_OPERATIONS.labels(operation="get", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update a user."""
    with USER_OPERATION_DURATION.labels(operation="update").time():
        try:
            from shared.models import User
            
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                USER_OPERATIONS.labels(operation="update", status="error").inc()
                raise HTTPException(status_code=404, detail="User not found")
            
            # Update user fields
            update_data = user_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(user)
            
            USER_OPERATIONS.labels(operation="update", status="success").inc()
            return UserResponse.model_validate(user)
            
        except HTTPException:
            raise
        except Exception as e:
            USER_OPERATIONS.labels(operation="update", status="error").inc()
            await session.rollback()
            raise HTTPException(status_code=500, detail=str(e))


@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Delete a user."""
    with USER_OPERATION_DURATION.labels(operation="delete").time():
        try:
            from shared.models import User
            
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                USER_OPERATIONS.labels(operation="delete", status="error").inc()
                raise HTTPException(status_code=404, detail="User not found")
            
            await session.delete(user)
            await session.commit()
            
            USER_OPERATIONS.labels(operation="delete", status="success").inc()
            ACTIVE_USERS.dec()
            
            return {"message": "User deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            USER_OPERATIONS.labels(operation="delete", status="error").inc()
            await session.rollback()
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development"
    )