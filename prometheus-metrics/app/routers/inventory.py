"""Inventory management API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_session
from app.services.inventory_service import inventory_service
from app.models import Stock

router = APIRouter(prefix="/inventory", tags=["Inventory"])

# Pydantic models for API
class StockResponse(BaseModel):
    id: int
    product_id: int
    available_quantity: int
    reserved_quantity: int
    reorder_level: int
    last_updated: str

    class Config:
        from_attributes = True

class StockUpdate(BaseModel):
    available_quantity: int
    reorder_level: Optional[int] = None

@router.get("/{product_id}", response_model=StockResponse)
async def get_stock(
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get stock information for a product."""
    stock = await inventory_service.get_stock_by_product_id(session, product_id)
    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock information for product {product_id} not found"
        )
    return StockResponse.model_validate(stock)

@router.post("/{product_id}/reserve")
async def reserve_stock(
    product_id: int,
    quantity: int,
    order_id: int,
    expires_minutes: int = 30,
    session: AsyncSession = Depends(get_session)
):
    """Reserve stock for an order."""
    try:
        success = await inventory_service.reserve_stock(
            session, product_id, quantity, order_id, expires_minutes
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to reserve stock - insufficient quantity or product not found"
            )
        return {
            "message": "Stock reserved successfully",
            "product_id": product_id,
            "quantity": quantity,
            "order_id": order_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/orders/{order_id}/release")
async def release_reservation(
    order_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Release stock reservation for an order."""
    try:
        success = await inventory_service.release_reservation(session, order_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active reservations found for order {order_id}"
            )
        return {"message": f"Stock reservations for order {order_id} released successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )