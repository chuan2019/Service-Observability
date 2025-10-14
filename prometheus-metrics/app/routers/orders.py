"""Order management API endpoints."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_session
from app.services.order_service import order_service
from app.models import Order, OrderStatus

router = APIRouter(prefix="/orders", tags=["orders"])

# Pydantic models for API
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    user_id: int
    items: List[OrderItemCreate]
    shipping_address: Optional[str] = None
    notes: Optional[str] = None

class PaymentCreate(BaseModel):
    amount: float
    method: str  # credit_card, debit_card, paypal, etc.

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_amount: float
    status: str
    shipping_address: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True

class OrdersListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    size: int

@router.get("/", response_model=OrdersListResponse)
async def get_orders(
    skip: int = 0,
    limit: int = 50,
    user_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session)
):
    """Get orders with optional user filter and pagination."""
    if user_id:
        orders = await order_service.get_orders_by_user(session, user_id, skip=skip, limit=limit)
        total = len(orders)  # Simplified for user-specific orders
    else:
        # For now, we'll implement this as getting all orders (would need pagination in real app)
        orders = []  # Would implement get_all_orders method
        total = 0
    
    return OrdersListResponse(
        orders=[OrderResponse.model_validate(order) for order in orders],
        total=total,
        page=skip // limit + 1,
        size=len(orders)
    )

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific order by ID."""
    order = await order_service.get_order_by_id(session, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    return OrderResponse.model_validate(order)

@router.get("/user/{user_id}", response_model=OrdersListResponse)
async def get_user_orders(
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session)
):
    """Get all orders for a specific user."""
    orders = await order_service.get_orders_by_user(session, user_id, skip=skip, limit=limit)
    
    return OrdersListResponse(
        orders=[OrderResponse.model_validate(order) for order in orders],
        total=len(orders),  # Simplified
        page=skip // limit + 1,
        size=len(orders)
    )

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new order."""
    try:
        order = await order_service.create_order(session, order_data.model_dump())
        return OrderResponse.model_validate(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{order_id}/payment", response_model=OrderResponse)
async def process_order_payment(
    order_id: int,
    payment_data: PaymentCreate,
    session: AsyncSession = Depends(get_session)
):
    """Process payment for an order."""
    try:
        order = await order_service.process_order_payment(session, order_id, payment_data.model_dump())
        return OrderResponse.model_validate(order)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: int,
    reason: str = "customer_request",
    session: AsyncSession = Depends(get_session)
):
    """Cancel an order."""
    try:
        success = await order_service.cancel_order(session, order_id, reason)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found"
            )
        return {"message": f"Order {order_id} cancelled successfully", "reason": reason}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )