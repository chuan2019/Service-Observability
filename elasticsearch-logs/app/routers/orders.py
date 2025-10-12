"""Order management endpoints."""

import logging
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class OrderStatus(str, Enum):
    """Order status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Order(BaseModel):
    """Order model."""

    id: int
    user_id: int
    product_name: str
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime
    updated_at: datetime


class OrderCreate(BaseModel):
    """Order creation model."""

    user_id: int
    product_name: str
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)


class OrderUpdate(BaseModel):
    """Order update model."""

    status: OrderStatus | None = None
    quantity: int | None = Field(None, gt=0)
    price: float | None = Field(None, gt=0)


# Mock database
fake_orders_db = [
    Order(
        id=1,
        user_id=1,
        product_name="Laptop",
        quantity=1,
        price=999.99,
        status=OrderStatus.DELIVERED,
        created_at=datetime(2024, 1, 1, 10, 0, 0),
        updated_at=datetime(2024, 1, 3, 14, 30, 0),
    ),
    Order(
        id=2,
        user_id=2,
        product_name="Mouse",
        quantity=2,
        price=25.50,
        status=OrderStatus.PROCESSING,
        created_at=datetime(2024, 1, 2, 15, 30, 0),
        updated_at=datetime(2024, 1, 2, 15, 30, 0),
    ),
    Order(
        id=3,
        user_id=1,
        product_name="Keyboard",
        quantity=1,
        price=75.00,
        status=OrderStatus.SHIPPED,
        created_at=datetime(2024, 1, 3, 9, 15, 0),
        updated_at=datetime(2024, 1, 4, 11, 45, 0),
    ),
]


@router.get("/", response_model=list[Order])
async def get_orders(
    skip: int = Query(0, ge=0, description="Number of orders to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of orders to return"),
    status: OrderStatus | None = Query(None, description="Filter by order status"),
    user_id: int | None = Query(None, description="Filter by user ID"),
):
    """Get list of orders."""
    logger.info(
        "Fetching orders",
        extra={
            "event": "get_orders",
            "skip": skip,
            "limit": limit,
            "status_filter": status,
            "user_id_filter": user_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    orders = fake_orders_db

    # Apply filters
    if status:
        orders = [order for order in orders if order.status == status]

    if user_id:
        orders = [order for order in orders if order.user_id == user_id]

    result = orders[skip : skip + limit]

    logger.info(
        "Orders fetched successfully",
        extra={
            "event": "get_orders_success",
            "count": len(result),
            "total_available": len(orders),
            "filters_applied": {"status": status, "user_id": user_id},
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    return result


@router.get("/{order_id}", response_model=Order)
async def get_order(order_id: int):
    """Get order by ID."""
    logger.info(
        "Fetching order",
        extra={
            "event": "get_order",
            "order_id": order_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    order = next((order for order in fake_orders_db if order.id == order_id), None)

    if not order:
        logger.warning(
            "Order not found",
            extra={
                "event": "get_order_not_found",
                "order_id": order_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )
        raise HTTPException(status_code=404, detail="Order not found")

    logger.info(
        "Order fetched successfully",
        extra={
            "event": "get_order_success",
            "order_id": order_id,
            "order_status": order.status,
            "order_total": order.price * order.quantity,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    return order


@router.post("/", response_model=Order, status_code=201)
async def create_order(order_data: OrderCreate):
    """Create a new order."""
    logger.info(
        "Creating order",
        extra={
            "event": "create_order",
            "user_id": order_data.user_id,
            "product_name": order_data.product_name,
            "quantity": order_data.quantity,
            "price": order_data.price,
            "total": order_data.price * order_data.quantity,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    # Create new order
    new_id = max([order.id for order in fake_orders_db]) + 1
    now = datetime.utcnow()

    new_order = Order(
        id=new_id,
        user_id=order_data.user_id,
        product_name=order_data.product_name,
        quantity=order_data.quantity,
        price=order_data.price,
        status=OrderStatus.PENDING,
        created_at=now,
        updated_at=now,
    )

    fake_orders_db.append(new_order)

    logger.info(
        "Order created successfully",
        extra={
            "event": "create_order_success",
            "order_id": new_order.id,
            "user_id": new_order.user_id,
            "product_name": new_order.product_name,
            "total_value": new_order.price * new_order.quantity,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    return new_order


@router.put("/{order_id}", response_model=Order)
async def update_order(order_id: int, order_data: OrderUpdate):
    """Update an existing order."""
    logger.info(
        "Updating order",
        extra={
            "event": "update_order",
            "order_id": order_id,
            "update_fields": [
                k for k, v in order_data.model_dump(exclude_unset=True).items()
            ],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    order_index = next(
        (i for i, order in enumerate(fake_orders_db) if order.id == order_id), None
    )

    if order_index is None:
        logger.warning(
            "Order update failed - order not found",
            extra={
                "event": "update_order_not_found",
                "order_id": order_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )
        raise HTTPException(status_code=404, detail="Order not found")

    # Update order
    order = fake_orders_db[order_index]
    update_data = order_data.model_dump(exclude_unset=True)

    old_status = order.status

    for field, value in update_data.items():
        setattr(order, field, value)

    order.updated_at = datetime.utcnow()

    # Log status change if it occurred
    if "status" in update_data and old_status != order.status:
        logger.info(
            "Order status changed",
            extra={
                "event": "order_status_change",
                "order_id": order_id,
                "old_status": old_status,
                "new_status": order.status,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )

    logger.info(
        "Order updated successfully",
        extra={
            "event": "update_order_success",
            "order_id": order_id,
            "updated_fields": list(update_data.keys()),
            "current_status": order.status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    return order


@router.delete("/{order_id}")
async def cancel_order(order_id: int):
    """Cancel an order (soft delete by changing status)."""
    logger.info(
        "Cancelling order",
        extra={
            "event": "cancel_order",
            "order_id": order_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    order_index = next(
        (i for i, order in enumerate(fake_orders_db) if order.id == order_id), None
    )

    if order_index is None:
        logger.warning(
            "Order cancellation failed - order not found",
            extra={
                "event": "cancel_order_not_found",
                "order_id": order_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )
        raise HTTPException(status_code=404, detail="Order not found")

    order = fake_orders_db[order_index]

    # Check if order can be cancelled
    if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
        logger.warning(
            "Order cancellation failed - cannot cancel shipped/delivered order",
            extra={
                "event": "cancel_order_invalid_status",
                "order_id": order_id,
                "current_status": order.status,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )
        raise HTTPException(
            status_code=400, detail=f"Cannot cancel order with status: {order.status}"
        )

    old_status = order.status
    order.status = OrderStatus.CANCELLED
    order.updated_at = datetime.utcnow()

    logger.info(
        "Order cancelled successfully",
        extra={
            "event": "cancel_order_success",
            "order_id": order_id,
            "old_status": old_status,
            "new_status": order.status,
            "refund_amount": order.price * order.quantity,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    return {"message": "Order cancelled successfully", "order_id": order_id}
