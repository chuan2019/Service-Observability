"""Payment microservice main application."""

import os
import random
import sys
import uuid
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import REGISTRY, Counter, Gauge, Histogram, make_asgi_app
from shared.config import PaymentServiceSettings
from shared.database import get_db_manager, init_db_manager
from shared.middleware import PrometheusMiddleware
from shared.schemas import HealthResponse, PaymentCreate, PaymentResponse, PaymentStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models import Payment


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Metrics
PAYMENT_OPERATIONS = Counter(
    "payment_service_operations_total",
    "Total payment service operations",
    ["operation", "status"],
    registry=REGISTRY,
)

PAYMENT_OPERATION_DURATION = Histogram(
    "payment_service_operation_duration_seconds",
    "Payment service operation duration",
    ["operation"],
    registry=REGISTRY,
)

PAYMENT_AMOUNT = Histogram("payment_service_amount", "Payment amounts", ["status", "method"], registry=REGISTRY)

ACTIVE_PAYMENTS = Gauge("payment_service_active_payments", "Number of active payments", registry=REGISTRY)

settings = PaymentServiceSettings()


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
app.add_middleware(PrometheusMiddleware, service_name="payment-service")

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


@app.post("/payments", response_model=PaymentResponse)
async def process_payment(payment_data: PaymentCreate, session: AsyncSession = Depends(get_session)):
    """Process a payment."""
    with PAYMENT_OPERATION_DURATION.labels(operation="process").time():
        try:
            # Generate transaction ID
            transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"

            # Create payment record
            payment = Payment(
                order_id=payment_data.order_id,
                amount=payment_data.amount,
                payment_method=payment_data.payment_method,
                transaction_id=transaction_id,
                status=PaymentStatus.PENDING,
            )
            session.add(payment)
            await session.flush()

            # Simulate payment processing
            # In real world, this would call payment gateway API
            success = random.random() > 0.1  # 90% success rate

            if success:
                payment.status = PaymentStatus.COMPLETED
                payment.processed_at = datetime.utcnow()
                PAYMENT_OPERATIONS.labels(operation="process", status="success").inc()
                PAYMENT_AMOUNT.labels(status="completed", method=payment_data.payment_method).observe(
                    payment_data.amount
                )
            else:
                payment.status = PaymentStatus.FAILED
                PAYMENT_OPERATIONS.labels(operation="process", status="failed").inc()
                PAYMENT_AMOUNT.labels(status="failed", method=payment_data.payment_method).observe(payment_data.amount)

            await session.commit()
            await session.refresh(payment)

            return PaymentResponse.model_validate(payment)
        except Exception as e:
            await session.rollback()
            PAYMENT_OPERATIONS.labels(operation="process", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/payments", response_model=List[PaymentResponse])
async def list_payments(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session)):
    """Get all payments."""
    with PAYMENT_OPERATION_DURATION.labels(operation="list").time():
        try:
            result = await session.execute(select(Payment).offset(skip).limit(limit))
            payments = result.scalars().all()

            PAYMENT_OPERATIONS.labels(operation="list", status="success").inc()
            return [PaymentResponse.model_validate(payment) for payment in payments]
        except Exception as e:
            PAYMENT_OPERATIONS.labels(operation="list", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: int, session: AsyncSession = Depends(get_session)):
    """Get payment by ID."""
    with PAYMENT_OPERATION_DURATION.labels(operation="get").time():
        try:
            result = await session.execute(select(Payment).where(Payment.id == payment_id))
            payment = result.scalar_one_or_none()

            if not payment:
                PAYMENT_OPERATIONS.labels(operation="get", status="error").inc()
                raise HTTPException(status_code=404, detail="Payment not found")

            PAYMENT_OPERATIONS.labels(operation="get", status="success").inc()
            return PaymentResponse.model_validate(payment)
        except HTTPException:
            raise
        except Exception as e:
            PAYMENT_OPERATIONS.labels(operation="get", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/payments/order/{order_id}", response_model=List[PaymentResponse])
async def get_order_payments(order_id: int, session: AsyncSession = Depends(get_session)):
    """Get all payments for an order."""
    with PAYMENT_OPERATION_DURATION.labels(operation="get_order_payments").time():
        try:
            result = await session.execute(select(Payment).where(Payment.order_id == order_id))
            payments = result.scalars().all()

            PAYMENT_OPERATIONS.labels(operation="get_order_payments", status="success").inc()
            return [PaymentResponse.model_validate(payment) for payment in payments]
        except Exception as e:
            PAYMENT_OPERATIONS.labels(operation="get_order_payments", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/payments/{payment_id}/refund")
async def refund_payment(payment_id: int, session: AsyncSession = Depends(get_session)):
    """Refund a payment."""
    with PAYMENT_OPERATION_DURATION.labels(operation="refund").time():
        try:
            result = await session.execute(select(Payment).where(Payment.id == payment_id))
            payment = result.scalar_one_or_none()

            if not payment:
                PAYMENT_OPERATIONS.labels(operation="refund", status="error").inc()
                raise HTTPException(status_code=404, detail="Payment not found")

            if payment.status != PaymentStatus.COMPLETED:
                raise HTTPException(status_code=400, detail="Can only refund completed payments")

            payment.status = PaymentStatus.REFUNDED
            payment.updated_at = datetime.utcnow()

            await session.commit()

            PAYMENT_OPERATIONS.labels(operation="refund", status="success").inc()
            PAYMENT_AMOUNT.labels(status="refunded", method=payment.payment_method).observe(payment.amount)

            return {"status": "refunded", "payment_id": payment_id}
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            PAYMENT_OPERATIONS.labels(operation="refund", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
    )
