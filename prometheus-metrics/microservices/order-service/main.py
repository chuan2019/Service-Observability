"""Order microservice main application."""

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
from sqlalchemy.orm import selectinload
from typing import List, Optional
import httpx

from shared.config import OrderServiceSettings
from shared.database import init_db_manager, get_db_manager
from shared.schemas import OrderCreate, OrderResponse, OrderItemResponse, HealthResponse, OrderStatus


# Metrics
ORDER_OPERATIONS = Counter(
    'order_service_operations_total',
    'Total order service operations',
    ['operation', 'status'],
    registry=REGISTRY
)

ORDER_OPERATION_DURATION = Histogram(
    'order_service_operation_duration_seconds',
    'Order service operation duration',
    ['operation'],
    registry=REGISTRY
)

ACTIVE_ORDERS = Gauge(
    'order_service_active_orders',
    'Number of active orders',
    registry=REGISTRY
)

ORDER_VALUE = Histogram(
    'order_service_value',
    'Order values',
    ['status'],
    registry=REGISTRY
)

settings = OrderServiceSettings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Starting {settings.SERVICE_NAME}")
    init_db_manager(settings.DATABASE_URL)
    yield
    # Shutdown
    print(f"Shutting down {settings.SERVICE_NAME}")


app = FastAPI(
    title=settings.SERVICE_NAME,
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
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


@app.post("/orders", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new order."""
    with ORDER_OPERATION_DURATION.labels(operation="create").time():
        try:
            from shared.models import Order, OrderItem
            
            # Calculate total
            total_amount = sum(item.quantity * item.unit_price for item in order_data.items)
            
            # Create order
            order = Order(
                user_id=order_data.user_id,
                status=OrderStatus.PENDING,
                total_amount=total_amount
            )
            session.add(order)
            await session.flush()
            
            # Create order items
            for item_data in order_data.items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item_data.product_id,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                    total_price=item_data.quantity * item_data.unit_price
                )
                session.add(order_item)
            
            await session.commit()
            await session.refresh(order)
            
            # Load items
            result = await session.execute(
                select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
            )
            order = result.scalar_one()
            
            ORDER_OPERATIONS.labels(operation="create", status="success").inc()
            ACTIVE_ORDERS.inc()
            ORDER_VALUE.labels(status="pending").observe(total_amount)
            
            return OrderResponse.model_validate(order)
        except Exception as e:
            await session.rollback()
            ORDER_OPERATIONS.labels(operation="create", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders", response_model=List[OrderResponse])
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
):
    """Get all orders."""
    with ORDER_OPERATION_DURATION.labels(operation="list").time():
        try:
            from shared.models import Order
            
            result = await session.execute(
                select(Order).options(selectinload(Order.items)).offset(skip).limit(limit)
            )
            orders = result.scalars().all()
            
            ORDER_OPERATIONS.labels(operation="list", status="success").inc()
            return [OrderResponse.model_validate(order) for order in orders]
        except Exception as e:
            ORDER_OPERATIONS.labels(operation="list", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get order by ID."""
    with ORDER_OPERATION_DURATION.labels(operation="get").time():
        try:
            from shared.models import Order
            
            result = await session.execute(
                select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                ORDER_OPERATIONS.labels(operation="get", status="error").inc()
                raise HTTPException(status_code=404, detail="Order not found")
            
            ORDER_OPERATIONS.labels(operation="get", status="success").inc()
            return OrderResponse.model_validate(order)
        except HTTPException:
            raise
        except Exception as e:
            ORDER_OPERATIONS.labels(operation="get", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: int,
    status: OrderStatus,
    session: AsyncSession = Depends(get_session)
):
    """Update order status."""
    with ORDER_OPERATION_DURATION.labels(operation="update_status").time():
        try:
            from shared.models import Order
            
            result = await session.execute(
                select(Order).where(Order.id == order_id)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                ORDER_OPERATIONS.labels(operation="update_status", status="error").inc()
                raise HTTPException(status_code=404, detail="Order not found")
            
            old_status = order.status
            order.status = status
            order.updated_at = datetime.utcnow()
            
            await session.commit()
            
            ORDER_OPERATIONS.labels(operation="update_status", status="success").inc()
            
            if old_status == OrderStatus.PENDING and status != OrderStatus.PENDING:
                ACTIVE_ORDERS.dec()
            
            ORDER_VALUE.labels(status=status.value).observe(order.total_amount)
            
            return {"status": "updated", "order_id": order_id, "new_status": status}
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            ORDER_OPERATIONS.labels(operation="update_status", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    reason: str = "user_requested",
    session: AsyncSession = Depends(get_session)
):
    """Cancel an order."""
    with ORDER_OPERATION_DURATION.labels(operation="cancel").time():
        try:
            from shared.models import Order
            
            result = await session.execute(
                select(Order).where(Order.id == order_id)
            )
            order = result.scalar_one_or_none()
            
            if not order:
                ORDER_OPERATIONS.labels(operation="cancel", status="error").inc()
                raise HTTPException(status_code=404, detail="Order not found")
            
            if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot cancel order with status: {order.status}"
                )
            
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.utcnow()
            
            await session.commit()
            
            ORDER_OPERATIONS.labels(operation="cancel", status="success").inc()
            ACTIVE_ORDERS.dec()
            
            return {"status": "cancelled", "order_id": order_id, "reason": reason}
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            ORDER_OPERATIONS.labels(operation="cancel", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders/user/{user_id}", response_model=List[OrderResponse])
async def get_user_orders(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get all orders for a user."""
    with ORDER_OPERATION_DURATION.labels(operation="get_user_orders").time():
        try:
            from shared.models import Order
            
            result = await session.execute(
                select(Order).options(selectinload(Order.items)).where(Order.user_id == user_id)
            )
            orders = result.scalars().all()
            
            ORDER_OPERATIONS.labels(operation="get_user_orders", status="success").inc()
            return [OrderResponse.model_validate(order) for order in orders]
        except Exception as e:
            ORDER_OPERATIONS.labels(operation="get_user_orders", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
