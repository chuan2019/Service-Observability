"""Payment service with Prometheus metrics."""

import asyncio
import random
from typing import Any, Dict, List

from prometheus_client import Counter, Histogram, Gauge
from app.middleware.metrics import REGISTRY

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
    'payment_service_amount',
    'Payment amounts processed',
    ['payment_method', 'status'],
    registry=REGISTRY
)

PAYMENT_GATEWAY_CALLS = Counter(
    'payment_service_gateway_calls_total',
    'Total payment gateway calls',
    ['gateway', 'status'],
    registry=REGISTRY
)

FAILED_PAYMENTS = Counter(
    'payment_service_failed_payments_total',
    'Total failed payments',
    ['failure_reason'],
    registry=REGISTRY
)

PAYMENT_PROCESSING_QUEUE = Gauge(
    'payment_service_processing_queue',
    'Number of payments in processing queue',
    registry=REGISTRY
)


class PaymentService:
    """Service for processing payments with Prometheus metrics."""

    def __init__(self):
        self.payments: Dict[int, Dict[str, Any]] = {}
        self.next_id = 1001
        self.processing_queue = 0

    async def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment with comprehensive metrics."""
        with PAYMENT_OPERATION_DURATION.labels(operation="process_payment").time():
            self.processing_queue += 1
            PAYMENT_PROCESSING_QUEUE.set(self.processing_queue)
            
            try:
                # Validate payment data
                await self._validate_payment_data(payment_data)

                # Validate order exists
                await self._validate_order_exists(payment_data.get("order_id"))

                # Process with payment gateway
                gateway_response = await self._process_with_gateway(payment_data)

                # Record payment
                payment = await self._record_payment(payment_data, gateway_response)

                # Send payment confirmation
                await self._send_payment_confirmation(payment)

                # Record successful payment metrics
                payment_method = payment_data.get("method", "unknown")
                amount = payment_data.get("amount", 0.0)
                
                PAYMENT_AMOUNTS.labels(
                    payment_method=payment_method, 
                    status="success"
                ).observe(amount)
                
                PAYMENT_OPERATIONS.labels(
                    operation="process_payment", 
                    status="success"
                ).inc()

                return payment

            except Exception as e:
                # Record failed payment metrics
                payment_method = payment_data.get("method", "unknown")
                amount = payment_data.get("amount", 0.0)
                
                PAYMENT_AMOUNTS.labels(
                    payment_method=payment_method, 
                    status="failed"
                ).observe(amount)
                
                PAYMENT_OPERATIONS.labels(
                    operation="process_payment", 
                    status="error"
                ).inc()
                
                raise e
            finally:
                self.processing_queue -= 1
                PAYMENT_PROCESSING_QUEUE.set(self.processing_queue)

    async def _validate_payment_data(self, payment_data: Dict[str, Any]) -> None:
        """Validate payment data with metrics."""
        with PAYMENT_OPERATION_DURATION.labels(operation="validate_payment_data").time():
            try:
                # Simulate validation delay
                await asyncio.sleep(random.uniform(0.01, 0.03))

                required_fields = ["order_id", "amount", "method"]
                for field in required_fields:
                    if field not in payment_data:
                        FAILED_PAYMENTS.labels(failure_reason="missing_field").inc()
                        raise ValueError(f"Missing required field: {field}")

                amount = payment_data.get("amount", 0)
                if amount <= 0:
                    FAILED_PAYMENTS.labels(failure_reason="invalid_amount").inc()
                    raise ValueError("Payment amount must be greater than 0")

                if amount > 10000:  # Max payment limit
                    FAILED_PAYMENTS.labels(failure_reason="amount_too_large").inc()
                    raise ValueError("Payment amount exceeds maximum limit")

                valid_methods = ["credit_card", "debit_card", "paypal", "apple_pay", "google_pay"]
                if payment_data.get("method") not in valid_methods:
                    FAILED_PAYMENTS.labels(failure_reason="invalid_method").inc()
                    raise ValueError(f"Invalid payment method: {payment_data.get('method')}")

                PAYMENT_OPERATIONS.labels(operation="validate_payment_data", status="success").inc()

            except Exception as e:
                PAYMENT_OPERATIONS.labels(operation="validate_payment_data", status="error").inc()
                raise e

    async def _validate_order_exists(self, order_id: int) -> None:
        """Validate that the order exists."""
        with PAYMENT_OPERATION_DURATION.labels(operation="validate_order").time():
            try:
                # Cross-service validation
                from app.services.order_service import OrderService
                order_service = OrderService()
                
                # This will raise an exception if order doesn't exist
                await order_service.get_order(order_id)
                
                PAYMENT_OPERATIONS.labels(operation="validate_order", status="success").inc()

            except ValueError:
                FAILED_PAYMENTS.labels(failure_reason="order_not_found").inc()
                PAYMENT_OPERATIONS.labels(operation="validate_order", status="not_found").inc()
                raise ValueError(f"Order {order_id} not found")
            except Exception as e:
                PAYMENT_OPERATIONS.labels(operation="validate_order", status="error").inc()
                raise e

    async def _process_with_gateway(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment with external gateway."""
        with PAYMENT_OPERATION_DURATION.labels(operation="gateway_call").time():
            try:
                payment_method = payment_data.get("method", "credit_card")
                
                # Simulate different gateway processing times
                gateway_delays = {
                    "credit_card": (0.1, 0.3),
                    "debit_card": (0.08, 0.25),
                    "paypal": (0.15, 0.4),
                    "apple_pay": (0.05, 0.15),
                    "google_pay": (0.05, 0.15),
                }
                
                delay_range = gateway_delays.get(payment_method, (0.1, 0.3))
                await asyncio.sleep(random.uniform(*delay_range))

                # Simulate gateway failures (5% chance)
                if random.random() < 0.05:
                    PAYMENT_GATEWAY_CALLS.labels(gateway=payment_method, status="failed").inc()
                    FAILED_PAYMENTS.labels(failure_reason="gateway_error").inc()
                    raise ValueError("Payment gateway temporarily unavailable")

                # Simulate declined payments (3% chance)
                if random.random() < 0.03:
                    PAYMENT_GATEWAY_CALLS.labels(gateway=payment_method, status="declined").inc()
                    FAILED_PAYMENTS.labels(failure_reason="card_declined").inc()
                    raise ValueError("Payment declined by gateway")

                # Successful gateway response
                PAYMENT_GATEWAY_CALLS.labels(gateway=payment_method, status="success").inc()
                
                return {
                    "gateway_transaction_id": f"gw_{random.randint(100000, 999999)}",
                    "gateway_status": "approved",
                    "gateway_response_code": "00",
                    "gateway_message": "Transaction approved",
                    "processing_fee": round(payment_data["amount"] * 0.029, 2),  # 2.9% fee
                }

            except Exception as e:
                PAYMENT_OPERATIONS.labels(operation="gateway_call", status="error").inc()
                raise e

    async def _record_payment(self, payment_data: Dict[str, Any], gateway_response: Dict[str, Any]) -> Dict[str, Any]:
        """Record payment in database."""
        with PAYMENT_OPERATION_DURATION.labels(operation="record_payment").time():
            try:
                # Simulate database write delay
                await asyncio.sleep(random.uniform(0.02, 0.08))

                payment_id = self.next_id
                self.next_id += 1

                payment = {
                    "id": payment_id,
                    "order_id": payment_data["order_id"],
                    "amount": payment_data["amount"],
                    "method": payment_data["method"],
                    "status": "completed",
                    "gateway_transaction_id": gateway_response["gateway_transaction_id"],
                    "processing_fee": gateway_response["processing_fee"],
                    "net_amount": payment_data["amount"] - gateway_response["processing_fee"],
                    "created_at": "2024-01-15T10:30:00Z",
                    "processed_at": "2024-01-15T10:30:15Z",
                }

                self.payments[payment_id] = payment
                PAYMENT_OPERATIONS.labels(operation="record_payment", status="success").inc()

                return payment.copy()

            except Exception as e:
                PAYMENT_OPERATIONS.labels(operation="record_payment", status="error").inc()
                raise e

    async def _send_payment_confirmation(self, payment: Dict[str, Any]) -> None:
        """Send payment confirmation to external systems."""
        with PAYMENT_OPERATION_DURATION.labels(operation="send_confirmation").time():
            try:
                # Simulate sending confirmation email/notification
                await asyncio.sleep(random.uniform(0.05, 0.15))

                # Simulate occasional notification failures (2% chance)
                if random.random() < 0.02:
                    PAYMENT_OPERATIONS.labels(operation="send_confirmation", status="failed").inc()
                    # Don't fail the entire payment for notification failures
                    print(f"Failed to send payment confirmation for payment {payment['id']}")
                    return

                PAYMENT_OPERATIONS.labels(operation="send_confirmation", status="success").inc()

            except Exception as e:
                PAYMENT_OPERATIONS.labels(operation="send_confirmation", status="error").inc()
                # Don't propagate confirmation failures
                print(f"Error sending payment confirmation: {e}")

    async def get_payment(self, payment_id: int) -> Dict[str, Any]:
        """Get payment by ID with metrics."""
        with PAYMENT_OPERATION_DURATION.labels(operation="get_payment").time():
            try:
                # Simulate database query delay
                await asyncio.sleep(random.uniform(0.01, 0.04))

                if payment_id not in self.payments:
                    PAYMENT_OPERATIONS.labels(operation="get_payment", status="not_found").inc()
                    raise ValueError(f"Payment {payment_id} not found")

                payment = self.payments[payment_id].copy()
                PAYMENT_OPERATIONS.labels(operation="get_payment", status="success").inc()
                
                return payment

            except Exception as e:
                PAYMENT_OPERATIONS.labels(operation="get_payment", status="error").inc()
                raise e

    async def get_payments_by_order(self, order_id: int) -> List[Dict[str, Any]]:
        """Get all payments for an order."""
        with PAYMENT_OPERATION_DURATION.labels(operation="get_payments_by_order").time():
            try:
                # Simulate database query delay
                await asyncio.sleep(random.uniform(0.02, 0.06))

                payments = [payment.copy() for payment in self.payments.values() 
                           if payment["order_id"] == order_id]
                
                PAYMENT_OPERATIONS.labels(operation="get_payments_by_order", status="success").inc()
                return payments

            except Exception as e:
                PAYMENT_OPERATIONS.labels(operation="get_payments_by_order", status="error").inc()
                raise e

    async def refund_payment(self, payment_id: int, refund_amount: float = None, reason: str = "user_requested") -> Dict[str, Any]:
        """Process a refund with metrics."""
        with PAYMENT_OPERATION_DURATION.labels(operation="refund_payment").time():
            try:
                if payment_id not in self.payments:
                    PAYMENT_OPERATIONS.labels(operation="refund_payment", status="not_found").inc()
                    raise ValueError(f"Payment {payment_id} not found")

                payment = self.payments[payment_id]
                
                if payment["status"] != "completed":
                    FAILED_PAYMENTS.labels(failure_reason="invalid_payment_status").inc()
                    PAYMENT_OPERATIONS.labels(operation="refund_payment", status="invalid_status").inc()
                    raise ValueError(f"Cannot refund payment with status: {payment['status']}")

                # Default to full refund
                if refund_amount is None:
                    refund_amount = payment["amount"]
                
                if refund_amount > payment["amount"]:
                    FAILED_PAYMENTS.labels(failure_reason="refund_amount_too_large").inc()
                    PAYMENT_OPERATIONS.labels(operation="refund_payment", status="invalid_amount").inc()
                    raise ValueError("Refund amount cannot exceed original payment amount")

                # Simulate refund processing with gateway
                await asyncio.sleep(random.uniform(0.1, 0.3))

                # Create refund record
                refund_id = self.next_id
                self.next_id += 1

                refund = {
                    "id": refund_id,
                    "original_payment_id": payment_id,
                    "order_id": payment["order_id"],
                    "amount": refund_amount,
                    "status": "completed",
                    "reason": reason,
                    "created_at": "2024-01-15T10:30:00Z",
                    "processed_at": "2024-01-15T10:30:15Z",
                }

                # Update original payment status if full refund
                if refund_amount == payment["amount"]:
                    payment["status"] = "refunded"
                else:
                    payment["status"] = "partially_refunded"

                # Record refund metrics
                PAYMENT_AMOUNTS.labels(
                    payment_method=payment["method"], 
                    status="refunded"
                ).observe(refund_amount)
                
                PAYMENT_OPERATIONS.labels(operation="refund_payment", status="success").inc()

                return refund

            except Exception as e:
                PAYMENT_OPERATIONS.labels(operation="refund_payment", status="error").inc()
                raise e