"""Payment management API endpoints."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_session
from app.services.payment_service import payment_service
from app.models import Payment, PaymentStatus

router = APIRouter(prefix="/payments", tags=["payments"])

# Pydantic models for API
class PaymentCreate(BaseModel):
    order_id: int
    amount: float
    method: str  # credit_card, debit_card, paypal, etc.

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    status: str
    payment_method: str
    transaction_id: Optional[str] = None
    processed_at: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific payment by ID."""
    payment = await payment_service.get_payment_by_id(session, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment {payment_id} not found"
        )
    return PaymentResponse.model_validate(payment)

@router.get("/order/{order_id}")
async def get_order_payments(
    order_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get all payments for an order."""
    payments = await payment_service.get_payments_by_order(session, order_id)
    return {
        "order_id": order_id,
        "payments": [PaymentResponse.model_validate(payment) for payment in payments]
    }

@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def process_payment(
    payment_data: PaymentCreate,
    session: AsyncSession = Depends(get_session)
):
    """Process a payment."""
    try:
        payment = await payment_service.process_payment(session, payment_data.model_dump())
        return PaymentResponse.model_validate(payment)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )