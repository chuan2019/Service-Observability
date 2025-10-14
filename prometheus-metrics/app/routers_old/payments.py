"""Payment processing API routes with Prometheus metrics."""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services.payment_service import PaymentService

router = APIRouter()
payment_service = PaymentService()


class PaymentCreateModel(BaseModel):
    """Model for processing a payment."""
    order_id: int
    amount: float
    method: str  # credit_card, debit_card, paypal, apple_pay, google_pay


class RefundCreateModel(BaseModel):
    """Model for processing a refund."""
    amount: float = None  # If None, full refund
    reason: str = "user_requested"


class PaymentResponseModel(BaseModel):
    """Model for payment response."""
    id: int
    order_id: int
    amount: float
    method: str
    status: str
    gateway_transaction_id: str
    processing_fee: float
    net_amount: float
    created_at: str
    processed_at: str


class RefundResponseModel(BaseModel):
    """Model for refund response."""
    id: int
    original_payment_id: int
    order_id: int
    amount: float
    status: str
    reason: str
    created_at: str
    processed_at: str


@router.post("/", response_model=PaymentResponseModel, status_code=status.HTTP_201_CREATED)
async def process_payment(payment_data: PaymentCreateModel):
    """Process a payment."""
    try:
        payment = await payment_service.process_payment(payment_data.dict())
        return payment
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        elif any(keyword in error_msg for keyword in ["invalid", "missing", "declined", "exceeds"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment processing failed: {str(e)}"
        )


@router.get("/{payment_id}", response_model=PaymentResponseModel)
async def get_payment(payment_id: int):
    """Get payment by ID."""
    try:
        payment = await payment_service.get_payment(payment_id)
        return payment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve payment: {str(e)}"
        )


@router.get("/order/{order_id}", response_model=List[PaymentResponseModel])
async def get_payments_by_order(order_id: int):
    """Get all payments for a specific order."""
    try:
        payments = await payment_service.get_payments_by_order(order_id)
        return payments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve payments for order: {str(e)}"
        )


@router.post("/{payment_id}/refund", response_model=RefundResponseModel, status_code=status.HTTP_201_CREATED)
async def refund_payment(payment_id: int, refund_data: RefundCreateModel):
    """Process a refund for a payment."""
    try:
        refund = await payment_service.refund_payment(
            payment_id,
            refund_data.amount,
            refund_data.reason
        )
        return refund
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        elif any(keyword in error_msg for keyword in ["invalid", "cannot", "exceeds"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=error_msg
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refund processing failed: {str(e)}"
        )