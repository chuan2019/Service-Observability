"""Inventory microservice main application."""

import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List
import uvicorn

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import REGISTRY, Counter, Gauge, Histogram, make_asgi_app
from shared.config import InventoryServiceSettings
from shared.database import get_db_manager, init_db_manager
from shared.middleware import PrometheusMiddleware
from shared.schemas import HealthResponse, StockCreate, StockResponse, StockUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models import Stock, StockReservation


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Metrics
INVENTORY_OPERATIONS = Counter(
    "inventory_service_operations_total",
    "Total inventory service operations",
    ["operation", "status"],
    registry=REGISTRY,
)

INVENTORY_OPERATION_DURATION = Histogram(
    "inventory_service_operation_duration_seconds",
    "Inventory service operation duration",
    ["operation"],
    registry=REGISTRY,
)

STOCK_LEVEL = Gauge("inventory_service_stock_level", "Current stock levels", ["product_id"], registry=REGISTRY)

settings = InventoryServiceSettings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Starting {settings.SERVICE_NAME}")
    init_db_manager(settings.DATABASE_URL)
    yield
    # Shutdown
    print(f"Shutting down {settings.SERVICE_NAME}")


app = FastAPI(title=settings.SERVICE_NAME, version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus middleware for automatic HTTP metrics
app.add_middleware(PrometheusMiddleware, service_name="inventory-service")

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
    return HealthResponse(status="healthy", service=settings.SERVICE_NAME, timestamp=datetime.utcnow())


@app.get("/inventory", response_model=List[StockResponse])
async def list_inventory(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session)):
    """Get all inventory items."""
    with INVENTORY_OPERATION_DURATION.labels(operation="list").time():
        try:
            result = await session.execute(select(Stock).offset(skip).limit(limit))
            stocks = result.scalars().all()

            INVENTORY_OPERATIONS.labels(operation="list", status="success").inc()
            return [StockResponse.model_validate(stock) for stock in stocks]
        except Exception as e:
            INVENTORY_OPERATIONS.labels(operation="list", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/inventory", response_model=StockResponse, status_code=201)
async def create_stock(stock_data: StockCreate, session: AsyncSession = Depends(get_session)):
    """Create stock for a product."""
    with INVENTORY_OPERATION_DURATION.labels(operation="create").time():
        try:
            # Check if stock already exists for this product
            result = await session.execute(select(Stock).where(Stock.product_id == stock_data.product_id))
            existing_stock = result.scalar_one_or_none()

            if existing_stock:
                INVENTORY_OPERATIONS.labels(operation="create", status="error").inc()
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock already exists for product_id {stock_data.product_id}",
                )

            # Create new stock
            new_stock = Stock(
                product_id=stock_data.product_id,
                available_quantity=stock_data.available_quantity,
                reserved_quantity=stock_data.reserved_quantity,
                reorder_level=stock_data.reorder_level,
                last_updated=datetime.utcnow(),
            )

            session.add(new_stock)
            await session.commit()
            await session.refresh(new_stock)

            INVENTORY_OPERATIONS.labels(operation="create", status="success").inc()
            STOCK_LEVEL.labels(product_id=stock_data.product_id).set(stock_data.available_quantity)
            return StockResponse.model_validate(new_stock)
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            INVENTORY_OPERATIONS.labels(operation="create", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/inventory/{product_id}", response_model=StockResponse)
async def get_stock(product_id: int, session: AsyncSession = Depends(get_session)):
    """Get stock for a product."""
    with INVENTORY_OPERATION_DURATION.labels(operation="get").time():
        try:
            result = await session.execute(select(Stock).where(Stock.product_id == product_id))
            stock = result.scalar_one_or_none()

            if not stock:
                INVENTORY_OPERATIONS.labels(operation="get", status="error").inc()
                raise HTTPException(status_code=404, detail="Stock not found")

            INVENTORY_OPERATIONS.labels(operation="get", status="success").inc()
            STOCK_LEVEL.labels(product_id=product_id).set(stock.available_quantity)
            return StockResponse.model_validate(stock)
        except HTTPException:
            raise
        except Exception as e:
            INVENTORY_OPERATIONS.labels(operation="get", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.put("/inventory/{product_id}", response_model=StockResponse)
async def update_stock(product_id: int, stock_update: StockUpdate, session: AsyncSession = Depends(get_session)):
    """Update stock for a product."""
    with INVENTORY_OPERATION_DURATION.labels(operation="update").time():
        try:
            result = await session.execute(select(Stock).where(Stock.product_id == product_id))
            stock = result.scalar_one_or_none()

            if not stock:
                INVENTORY_OPERATIONS.labels(operation="update", status="error").inc()
                raise HTTPException(status_code=404, detail="Stock not found")

            # Update fields
            if stock_update.available_quantity is not None:
                stock.available_quantity = stock_update.available_quantity
            if stock_update.reserved_quantity is not None:
                stock.reserved_quantity = stock_update.reserved_quantity
            if stock_update.reorder_level is not None:
                stock.reorder_level = stock_update.reorder_level

            stock.last_updated = datetime.utcnow()

            await session.commit()
            await session.refresh(stock)

            INVENTORY_OPERATIONS.labels(operation="update", status="success").inc()
            STOCK_LEVEL.labels(product_id=product_id).set(stock.available_quantity)
            return StockResponse.model_validate(stock)
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            INVENTORY_OPERATIONS.labels(operation="update", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/inventory/{product_id}/reserve")
async def reserve_stock(product_id: int, quantity: int, order_id: int, session: AsyncSession = Depends(get_session)):
    """Reserve stock for an order."""
    with INVENTORY_OPERATION_DURATION.labels(operation="reserve").time():
        try:
            result = await session.execute(select(Stock).where(Stock.product_id == product_id))
            stock = result.scalar_one_or_none()

            if not stock:
                INVENTORY_OPERATIONS.labels(operation="reserve", status="error").inc()
                raise HTTPException(status_code=404, detail="Stock not found")

            available = stock.available_quantity - stock.reserved_quantity
            if available < quantity:
                INVENTORY_OPERATIONS.labels(operation="reserve", status="error").inc()
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock. Available: {available}, Requested: {quantity}",
                )

            # Create reservation
            reservation = StockReservation(
                stock_id=stock.id,
                order_id=order_id,
                quantity=quantity,
            )
            session.add(reservation)

            # Update reserved quantity
            stock.reserved_quantity += quantity
            stock.last_updated = datetime.utcnow()

            await session.commit()

            INVENTORY_OPERATIONS.labels(operation="reserve", status="success").inc()
            STOCK_LEVEL.labels(product_id=product_id).set(stock.available_quantity - stock.reserved_quantity)
            return {"status": "reserved", "quantity": quantity}
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            INVENTORY_OPERATIONS.labels(operation="reserve", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/inventory/orders/{order_id}/release")
async def release_reservation(order_id: int, session: AsyncSession = Depends(get_session)):
    """Release stock reservation for an order."""
    with INVENTORY_OPERATION_DURATION.labels(operation="release").time():
        try:
            result = await session.execute(select(StockReservation).where(StockReservation.order_id == order_id))
            reservations = result.scalars().all()

            if not reservations:
                return {"status": "no_reservations"}

            for reservation in reservations:
                stock_result = await session.execute(select(Stock).where(Stock.id == reservation.stock_id))
                stock = stock_result.scalar_one_or_none()

                if stock:
                    stock.reserved_quantity -= reservation.quantity
                    stock.last_updated = datetime.utcnow()
                    STOCK_LEVEL.labels(product_id=stock.product_id).set(stock.available_quantity - stock.reserved_quantity)

                await session.delete(reservation)

            await session.commit()

            INVENTORY_OPERATIONS.labels(operation="release", status="success").inc()
            return {"status": "released"}
        except Exception as e:
            await session.rollback()
            INVENTORY_OPERATIONS.labels(operation="release", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
