"""Payment service with distributed tracing."""

import asyncio
import random
from typing import Dict, Any

from config import get_tracer

tracer = get_tracer(__name__)


class PaymentService:
    """Service for processing payments with tracing."""
    
    def __init__(self):
        self.payments: Dict[int, Dict[str, Any]] = {}
        self.next_id = 1001
    
    async def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment with tracing."""
        with tracer.start_as_current_span("payment_service.process_payment") as span:
            span.set_attribute("service", "payment")
            span.set_attribute("operation", "process_payment")
            span.set_attribute("payment.order_id", payment_data.get("order_id", 0))
            span.set_attribute("payment.amount", payment_data.get("amount", 0.0))
            span.set_attribute("payment.method", payment_data.get("method", ""))
            
            # Validate payment data
            await self._validate_payment_data(payment_data)
            
            # Process with payment gateway
            gateway_response = await self._process_with_gateway(payment_data)
            
            # Record payment
            payment = await self._record_payment(payment_data, gateway_response)
            
            # Send payment confirmation
            await self._send_payment_confirmation(payment)
            
            return payment
    
    async def _validate_payment_data(self, payment_data: Dict[str, Any]) -> None:
        """Validate payment data with tracing."""
        with tracer.start_as_current_span("payment_service.validate_payment_data") as span:
            span.set_attribute("service", "payment")
            span.set_attribute("operation", "validate_payment_data")
            
            # Simulate validation delay
            await asyncio.sleep(random.uniform(0.005, 0.02))
            
            required_fields = ["order_id", "amount", "method"]
            missing_fields = [field for field in required_fields if field not in payment_data]
            
            if missing_fields:
                span.set_attribute("validation.success", False)
                span.set_attribute("validation.missing_fields", str(missing_fields))
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            if payment_data.get("amount", 0) <= 0:
                span.set_attribute("validation.success", False)
                span.set_attribute("validation.error", "invalid_amount")
                raise ValueError("Payment amount must be positive")
            
            valid_methods = ["credit_card", "debit_card", "paypal", "bank_transfer"]
            if payment_data.get("method") not in valid_methods:
                span.set_attribute("validation.success", False)
                span.set_attribute("validation.error", "invalid_method")
                raise ValueError(f"Invalid payment method. Must be one of: {valid_methods}")
            
            span.set_attribute("validation.success", True)
    
    async def _process_with_gateway(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process payment with gateway with tracing."""
        with tracer.start_as_current_span("payment_service.gateway_processing") as span:
            span.set_attribute("service", "payment")
            span.set_attribute("operation", "gateway_processing")
            span.set_attribute("gateway.provider", "mock_gateway")
            span.set_attribute("gateway.method", payment_data["method"])
            span.set_attribute("gateway.amount", payment_data["amount"])
            
            # Simulate different processing times based on payment method
            method_delays = {
                "credit_card": (0.1, 0.3),
                "debit_card": (0.08, 0.25),
                "paypal": (0.05, 0.15),
                "bank_transfer": (0.2, 0.5)
            }
            
            delay_range = method_delays.get(payment_data["method"], (0.1, 0.3))
            processing_time = random.uniform(*delay_range)
            await asyncio.sleep(processing_time)
            
            span.set_attribute("gateway.processing_time", processing_time)
            
            # Simulate payment success/failure - 90% success rate
            success = random.random() > 0.1
            
            if success:
                transaction_id = f"txn_{random.randint(100000, 999999)}"
                response = {
                    "status": "success",
                    "transaction_id": transaction_id,
                    "gateway_fee": payment_data["amount"] * 0.029,  # 2.9% fee
                    "processing_time": processing_time
                }
                span.set_attribute("gateway.success", True)
                span.set_attribute("gateway.transaction_id", transaction_id)
                span.set_attribute("gateway.fee", response["gateway_fee"])
            else:
                error_codes = ["insufficient_funds", "card_declined", "expired_card", "invalid_cvv"]
                error_code = random.choice(error_codes)
                response = {
                    "status": "failed",
                    "error_code": error_code,
                    "error_message": f"Payment failed: {error_code.replace('_', ' ')}"
                }
                span.set_attribute("gateway.success", False)
                span.set_attribute("gateway.error_code", error_code)
            
            return response
    
    async def _record_payment(self, payment_data: Dict[str, Any], gateway_response: Dict[str, Any]) -> Dict[str, Any]:
        """Record payment in database with tracing."""
        with tracer.start_as_current_span("payment_service.record_payment") as span:
            span.set_attribute("service", "payment")
            span.set_attribute("operation", "record_payment")
            
            # Simulate database save delay
            await asyncio.sleep(random.uniform(0.01, 0.05))
            
            payment = {
                "id": self.next_id,
                "order_id": payment_data["order_id"],
                "amount": payment_data["amount"],
                "method": payment_data["method"],
                "status": gateway_response["status"],
                "transaction_id": gateway_response.get("transaction_id"),
                "error_code": gateway_response.get("error_code"),
                "gateway_fee": gateway_response.get("gateway_fee", 0.0),
                "processing_time": gateway_response.get("processing_time", 0.0)
            }
            
            # Raise exception for failed payments
            if payment["status"] == "failed":
                span.set_attribute("payment.recorded", False)
                span.set_attribute("payment.error", payment["error_code"])
                raise ValueError(f"Payment failed: {gateway_response.get('error_message', 'Unknown error')}")
            
            self.payments[self.next_id] = payment
            span.set_attribute("payment.recorded", True)
            span.set_attribute("payment.id", self.next_id)
            self.next_id += 1
            
            return payment
    
    async def _send_payment_confirmation(self, payment: Dict[str, Any]) -> None:
        """Send payment confirmation with tracing."""
        with tracer.start_as_current_span("payment_service.send_confirmation") as span:
            span.set_attribute("service", "payment")
            span.set_attribute("operation", "send_confirmation")
            span.set_attribute("confirmation.payment_id", payment["id"])
            span.set_attribute("confirmation.order_id", payment["order_id"])
            
            # Simulate confirmation service call
            await asyncio.sleep(random.uniform(0.01, 0.03))
            
            # Mock confirmation - randomly fail 1% of the time
            if random.random() < 0.01:
                span.set_attribute("confirmation.success", False)
                span.set_attribute("confirmation.error", "delivery_failed")
                # Don't raise error for confirmation failures - just log
                return
            
            span.set_attribute("confirmation.success", True)
            span.set_attribute("confirmation.type", "email_and_sms")
    
    async def get_payment(self, payment_id: int) -> Dict[str, Any]:
        """Get payment by ID with tracing."""
        with tracer.start_as_current_span("payment_service.get_payment") as span:
            span.set_attribute("service", "payment")
            span.set_attribute("operation", "get_payment")
            span.set_attribute("payment_id", payment_id)
            
            # Simulate database lookup delay
            await asyncio.sleep(random.uniform(0.01, 0.05))
            
            if payment_id not in self.payments:
                span.set_attribute("payment.found", False)
                span.set_attribute("error.type", "not_found")
                raise ValueError(f"Payment {payment_id} not found")
            
            payment = self.payments[payment_id]
            span.set_attribute("payment.found", True)
            span.set_attribute("payment.status", payment["status"])
            span.set_attribute("payment.amount", payment["amount"])
            
            return payment
    
    async def refund_payment(self, payment_id: int, amount: float = None) -> Dict[str, Any]:
        """Process a refund with tracing."""
        with tracer.start_as_current_span("payment_service.refund_payment") as span:
            span.set_attribute("service", "payment")
            span.set_attribute("operation", "refund_payment")
            span.set_attribute("payment_id", payment_id)
            
            # Get original payment
            payment = await self.get_payment(payment_id)
            
            refund_amount = amount or payment["amount"]
            span.set_attribute("refund.amount", refund_amount)
            
            if refund_amount > payment["amount"]:
                span.set_attribute("refund.valid", False)
                raise ValueError("Refund amount cannot exceed original payment amount")
            
            # Simulate refund processing
            await asyncio.sleep(random.uniform(0.05, 0.15))
            
            # Mock refund - 95% success rate
            if random.random() > 0.05:
                refund = {
                    "id": self.next_id,
                    "original_payment_id": payment_id,
                    "amount": refund_amount,
                    "status": "completed",
                    "refund_id": f"ref_{random.randint(100000, 999999)}"
                }
                self.next_id += 1
                span.set_attribute("refund.success", True)
                span.set_attribute("refund.id", refund["refund_id"])
            else:
                span.set_attribute("refund.success", False)
                raise ValueError("Refund processing failed")
            
            return refund