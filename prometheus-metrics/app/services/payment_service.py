"""Payment service with database operations and Prometheus metrics."""

import random
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from prometheus_client import Counter, Histogram, Gauge

from app.middleware.metrics import REGISTRY
from app.models import Payment, Refund, Order, PaymentStatus

# Payment service specific metrics
PAYMENT_OPERATIONS = Counter(
    'payment_service_operations_total',
    'Total payment service operations',
    ['operation', 'status'],
    registry=REGISTRY
)

PAYMENT_OPERATION_DURATION = Histogram(
    'payment_service_operation_duration_seconds',
    'Payment service operation duration',
    ['operation'],
    registry=REGISTRY
)

PAYMENT_AMOUNTS = Histogram(
    'payment_service_amounts',
    'Payment amounts processed',
    ['payment_method', 'status'],
    registry=REGISTRY
)

PAYMENT_GATEWAY_CALLS = Counter(
    'payment_service_gateway_calls_total',
    'Total payment gateway API calls',
    ['gateway', 'operation', 'status'],
    registry=REGISTRY
)

FAILED_PAYMENTS = Counter(
    'payment_service_failed_payments_total',
    'Total failed payments',
    ['payment_method', 'failure_reason'],
    registry=REGISTRY
)

PAYMENT_PROCESSING_QUEUE = Gauge(
    'payment_service_processing_queue',
    'Number of payments currently being processed',
    registry=REGISTRY
)

PAYMENT_DATABASE_QUERIES = Counter(
    'payment_service_db_queries_total',
    'Total database queries in payment service',
    ['query_type', 'status'],
    registry=REGISTRY
)


class PaymentService:
    """Service for managing payments with database operations and Prometheus metrics."""

    def __init__(self):
        """Initialize the payment service."""
        pass

    async def process_payment(self, session: AsyncSession, payment_data: Dict[str, Any]) -> Payment:
        """Process a payment for an order."""
        with PAYMENT_OPERATION_DURATION.labels(operation="process_payment").time():
            try:
                # Increment processing queue
                PAYMENT_PROCESSING_QUEUE.inc()
                
                PAYMENT_DATABASE_QUERIES.labels(query_type="insert", status="started").inc()
                
                # Validate order exists
                order_result = await session.execute(
                    select(Order).where(Order.id == payment_data["order_id"])
                )
                order = order_result.scalar_one_or_none()
                if not order:
                    PAYMENT_OPERATIONS.labels(operation="process_payment", status="order_not_found").inc()
                    raise ValueError(f"Order {payment_data['order_id']} not found")
                
                # Create payment record
                payment = Payment(
                    order_id=payment_data["order_id"],
                    amount=payment_data["amount"],
                    payment_method=payment_data["method"],
                    status=PaymentStatus.PENDING,
                    transaction_id=None,
                    gateway_response=None
                )
                
                session.add(payment)
                await session.commit()
                await session.refresh(payment)
                
                # Simulate payment gateway processing
                gateway_result = await self._simulate_payment_gateway(
                    payment.id, 
                    payment_data["amount"], 
                    payment_data["method"]
                )
                
                # Update payment with gateway result
                payment.transaction_id = gateway_result["transaction_id"]
                payment.gateway_response = gateway_result["response"]
                payment.status = PaymentStatus.COMPLETED if gateway_result["success"] else PaymentStatus.FAILED
                payment.processed_at = datetime.utcnow()
                
                await session.commit()
                await session.refresh(payment)
                
                PAYMENT_DATABASE_QUERIES.labels(query_type="insert", status="success").inc()
                
                if payment.status == PaymentStatus.COMPLETED:
                    PAYMENT_OPERATIONS.labels(operation="process_payment", status="success").inc()
                    PAYMENT_AMOUNTS.labels(
                        payment_method=payment_data["method"], 
                        status="success"
                    ).observe(payment_data["amount"])
                else:
                    PAYMENT_OPERATIONS.labels(operation="process_payment", status="failed").inc()
                    FAILED_PAYMENTS.labels(
                        payment_method=payment_data["method"],
                        failure_reason=gateway_result["response"].get("error", "unknown")
                    ).inc()
                
                return payment
                
            except Exception as e:
                await session.rollback()
                PAYMENT_DATABASE_QUERIES.labels(query_type="insert", status="error").inc()
                PAYMENT_OPERATIONS.labels(operation="process_payment", status="error").inc()
                raise
            finally:
                # Decrement processing queue
                PAYMENT_PROCESSING_QUEUE.dec()

    async def get_payment_by_id(self, session: AsyncSession, payment_id: int) -> Optional[Payment]:
        """Get a payment by ID."""
        with PAYMENT_OPERATION_DURATION.labels(operation="get_by_id").time():
            try:
                PAYMENT_DATABASE_QUERIES.labels(query_type="select", status="started").inc()
                
                result = await session.execute(
                    select(Payment).where(Payment.id == payment_id)
                )
                payment = result.scalar_one_or_none()
                
                PAYMENT_DATABASE_QUERIES.labels(query_type="select", status="success").inc()
                
                if payment:
                    PAYMENT_OPERATIONS.labels(operation="get_by_id", status="success").inc()
                else:
                    PAYMENT_OPERATIONS.labels(operation="get_by_id", status="not_found").inc()
                
                return payment
                
            except Exception as e:
                PAYMENT_DATABASE_QUERIES.labels(query_type="select", status="error").inc()
                PAYMENT_OPERATIONS.labels(operation="get_by_id", status="error").inc()
                raise

    async def _simulate_payment_gateway(self, payment_id: int, amount: float, method: str) -> Dict[str, Any]:
        """Simulate payment gateway processing."""
        # Simulate network delay
        import asyncio
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Record gateway call
        PAYMENT_GATEWAY_CALLS.labels(
            gateway="simulate", 
            operation="process_payment", 
            status="started"
        ).inc()
        
        # Simulate success/failure (90% success rate)
        success = random.random() > 0.1
        
        if success:
            PAYMENT_GATEWAY_CALLS.labels(
                gateway="simulate", 
                operation="process_payment", 
                status="success"
            ).inc()
            
            return {
                "success": True,
                "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
                "response": {
                    "status": "approved",
                    "authorization_code": f"auth_{random.randint(100000, 999999)}",
                    "gateway_reference": f"gw_{uuid.uuid4().hex[:8]}"
                }
            }
        else:
            PAYMENT_GATEWAY_CALLS.labels(
                gateway="simulate", 
                operation="process_payment", 
                status="failed"
            ).inc()
            
            failure_reasons = ["insufficient_funds", "card_declined", "expired_card", "invalid_cvv"]
            
            return {
                "success": False,
                "transaction_id": None,
                "response": {
                    "status": "declined",
                    "error": random.choice(failure_reasons),
                    "error_code": f"E{random.randint(1000, 9999)}"
                }
            }

# Global service instance
payment_service = PaymentService()