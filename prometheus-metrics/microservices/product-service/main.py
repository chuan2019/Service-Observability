"""Product microservice main application."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge, REGISTRY
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from shared.config import ProductServiceSettings
from shared.database import init_db_manager, get_db_manager
from shared.schemas import ProductCreate, ProductUpdate, ProductResponse, HealthResponse
from shared.models import Product

# Metrics
PRODUCT_OPERATIONS = Counter(
    'product_service_operations_total',
    'Total product service operations',
    ['operation', 'status'],
    registry=REGISTRY
)

PRODUCT_OPERATION_DURATION = Histogram(
    'product_service_operation_duration_seconds',
    'Product service operation duration',
    ['operation'],
    registry=REGISTRY
)

TOTAL_PRODUCTS = Gauge(
    'product_service_total_products',
    'Total number of products',
    registry=REGISTRY
)

settings = ProductServiceSettings()


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
    title="Product Service",
    description="Product catalog microservice",
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


@app.post("/products", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new product."""
    with PRODUCT_OPERATION_DURATION.labels(operation="create").time():
        try:
            # Check if product with SKU already exists
            existing_product = await session.execute(
                select(Product).where(Product.sku == product_data.sku)
            )
            if existing_product.scalar_one_or_none():
                PRODUCT_OPERATIONS.labels(operation="create", status="error").inc()
                raise HTTPException(status_code=400, detail="Product SKU already exists")
            
            # Create new product
            product = Product(**product_data.model_dump())
            session.add(product)
            await session.commit()
            await session.refresh(product)
            
            PRODUCT_OPERATIONS.labels(operation="create", status="success").inc()
            TOTAL_PRODUCTS.inc()
            
            return ProductResponse.model_validate(product)
            
        except Exception as e:
            PRODUCT_OPERATIONS.labels(operation="create", status="error").inc()
            await session.rollback()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/products", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    session: AsyncSession = Depends(get_session)
):
    """Get all products with optional category filter."""
    with PRODUCT_OPERATION_DURATION.labels(operation="list").time():
        try:
            query = select(Product).offset(skip).limit(limit)
            if category:
                query = query.where(Product.category == category)
            
            result = await session.execute(query)
            products = result.scalars().all()
            
            PRODUCT_OPERATIONS.labels(operation="list", status="success").inc()
            return [ProductResponse.model_validate(product) for product in products]
            
        except Exception as e:
            PRODUCT_OPERATIONS.labels(operation="list", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific product."""
    with PRODUCT_OPERATION_DURATION.labels(operation="get").time():
        try:
            result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()
            
            if not product:
                PRODUCT_OPERATIONS.labels(operation="get", status="error").inc()
                raise HTTPException(status_code=404, detail="Product not found")
            
            PRODUCT_OPERATIONS.labels(operation="get", status="success").inc()
            return ProductResponse.model_validate(product)
            
        except HTTPException:
            raise
        except Exception as e:
            PRODUCT_OPERATIONS.labels(operation="get", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update a product."""
    with PRODUCT_OPERATION_DURATION.labels(operation="update").time():
        try:
            result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()
            
            if not product:
                PRODUCT_OPERATIONS.labels(operation="update", status="error").inc()
                raise HTTPException(status_code=404, detail="Product not found")
            
            # Update product fields
            update_data = product_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(product, field, value)
            
            product.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(product)
            
            PRODUCT_OPERATIONS.labels(operation="update", status="success").inc()
            return ProductResponse.model_validate(product)
            
        except HTTPException:
            raise
        except Exception as e:
            PRODUCT_OPERATIONS.labels(operation="update", status="error").inc()
            await session.rollback()
            raise HTTPException(status_code=500, detail=str(e))


@app.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Delete a product."""
    with PRODUCT_OPERATION_DURATION.labels(operation="delete").time():
        try:
            result = await session.execute(
                select(Product).where(Product.id == product_id)
            )
            product = result.scalar_one_or_none()
            
            if not product:
                PRODUCT_OPERATIONS.labels(operation="delete", status="error").inc()
                raise HTTPException(status_code=404, detail="Product not found")
            
            await session.delete(product)
            await session.commit()
            
            PRODUCT_OPERATIONS.labels(operation="delete", status="success").inc()
            TOTAL_PRODUCTS.dec()
            
            return {"message": "Product deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            PRODUCT_OPERATIONS.labels(operation="delete", status="error").inc()
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