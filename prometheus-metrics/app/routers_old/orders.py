"""Order management API routes with Prometheus metrics."""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.order_service import OrderService

router = APIRouter()
order_service = OrderService()


class OrderCreateModel(BaseModel):
    """Model for creating a new order."""
    user_id: int
    amount: float
    items: List[str]
    type: str = "standard"


class OrderUpdateStatusModel(BaseModel):
    """Model for updating order status."""
    status: str
    reason: str = None


class OrderResponseModel(BaseModel):
    """Model for order response."""
    id: int
    user_id: int
    amount: float
    items: List[str]
    status: str
    type: str
    created_at: str
    updated_at: str = None
    estimated_delivery: str = None
    status_reason: str = None


@router.get("/", response_model=List[OrderResponseModel])
async def get_all_orders():
    """Get all orders."""
    try:
        orders = await order_service.get_all_orders()
        return orders
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve orders: {str(e)}"
        )


@router.get("/{order_id}", response_model=OrderResponseModel)
async def get_order(order_id: int):
    """Get order by ID."""
    try:
        order = await order_service.get_order(order_id)
        return order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve order: {str(e)}"
        )


@router.post("/", response_model=OrderResponseModel, status_code=status.HTTP_201_CREATED)
async def create_order(order_data: OrderCreateModel):
    """Create a new order."""
    try:
        order = await order_service.create_order(order_data.dict())
        return order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create order: {str(e)}"
        )


@router.put("/{order_id}/status", response_model=OrderResponseModel)
async def update_order_status(order_id: int, status_data: OrderUpdateStatusModel):
    """Update order status."""
    try:
        order = await order_service.update_order_status(
            order_id, 
            status_data.status, 
            status_data.reason
        )
        return order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update order status: {str(e)}"
        )


@router.post("/{order_id}/process", response_model=OrderResponseModel)
async def process_order(order_id: int):
    """Process an order (move from pending to processing)."""
    try:
        order = await order_service.process_order(order_id)
        return order
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process order: {str(e)}"
        )


@router.post("/{order_id}/cancel", response_model=OrderResponseModel)
async def cancel_order(order_id: int, reason: str = "user_requested"):
    """Cancel an order."""
    try:
        order = await order_service.cancel_order(order_id, reason)
        return order
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel order: {str(e)}"
        )


@router.get("/user/{user_id}", response_model=List[OrderResponseModel])
async def get_orders_by_user(user_id: int):
    """Get all orders for a specific user."""
    try:
        orders = await order_service.get_orders_by_user(user_id)
        return orders
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user orders: {str(e)}"
        )