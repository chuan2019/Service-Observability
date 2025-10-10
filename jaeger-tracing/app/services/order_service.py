"""Order service with distributed tracing."""

import asyncio
import random
from typing import Any, Dict, List

from config import get_tracer

tracer = get_tracer(__name__)


class OrderService:
    """Service for managing orders with tracing."""

    def __init__(self):
        self.orders: Dict[int, Dict[str, Any]] = {
            101: {
                "id": 101,
                "user_id": 1,
                "amount": 29.99,
                "items": ["item1", "item2"],
                "status": "completed",
            },
            102: {
                "id": 102,
                "user_id": 2,
                "amount": 49.99,
                "items": ["item3"],
                "status": "pending",
            },
        }
        self.next_id = 103

    async def get_order(self, order_id: int) -> Dict[str, Any]:
        """Get order by ID with tracing."""
        with tracer.start_as_current_span("order_service.get_order") as span:
            span.set_attribute("service", "order")
            span.set_attribute("operation", "get_order")
            span.set_attribute("order_id", order_id)

            # Simulate database lookup delay
            await asyncio.sleep(random.uniform(0.01, 0.05))

            if order_id not in self.orders:
                span.set_attribute("order.found", False)
                span.set_attribute("error.type", "not_found")
                raise ValueError(f"Order {order_id} not found")

            order = self.orders[order_id]
            span.set_attribute("order.found", True)
            span.set_attribute("order.user_id", order["user_id"])
            span.set_attribute("order.amount", order["amount"])
            span.set_attribute("order.status", order["status"])
            span.set_attribute("order.items_count", len(order["items"]))

            return order

    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order with tracing."""
        with tracer.start_as_current_span("order_service.create_order") as span:
            span.set_attribute("service", "order")
            span.set_attribute("operation", "create_order")
            span.set_attribute("order.user_id", order_data.get("user_id", 0))
            span.set_attribute("order.amount", order_data.get("amount", 0.0))

            # Validate order data
            await self._validate_order_data(order_data)

            # Check inventory
            await self._check_inventory(order_data.get("items", []))

            # Calculate order total
            total = await self._calculate_total(order_data)

            # Simulate database save delay
            await asyncio.sleep(random.uniform(0.02, 0.08))

            order = {
                "id": self.next_id,
                "user_id": order_data["user_id"],
                "amount": total,
                "items": order_data.get("items", []),
                "status": "pending",
            }

            self.orders[self.next_id] = order
            span.set_attribute("order.created_id", self.next_id)
            self.next_id += 1

            # Send order notification
            await self._send_order_notification(order)

            return order

    async def _validate_order_data(self, order_data: Dict[str, Any]) -> None:
        """Validate order data with tracing."""
        with tracer.start_as_current_span("order_service.validate_order_data") as span:
            span.set_attribute("service", "order")
            span.set_attribute("operation", "validate_order_data")

            # Simulate validation delay
            await asyncio.sleep(random.uniform(0.005, 0.02))

            required_fields = ["user_id", "amount"]
            missing_fields = [
                field for field in required_fields if field not in order_data
            ]

            if missing_fields:
                span.set_attribute("validation.success", False)
                span.set_attribute("validation.missing_fields", str(missing_fields))
                raise ValueError(f"Missing required fields: {missing_fields}")

            if order_data.get("amount", 0) <= 0:
                span.set_attribute("validation.success", False)
                span.set_attribute("validation.error", "invalid_amount")
                raise ValueError("Order amount must be positive")

            span.set_attribute("validation.success", True)

    async def _check_inventory(self, items: List[str]) -> None:
        """Check inventory availability with tracing."""
        with tracer.start_as_current_span("order_service.check_inventory") as span:
            span.set_attribute("service", "order")
            span.set_attribute("operation", "check_inventory")
            span.set_attribute("items.count", len(items))

            # Simulate inventory service call
            await asyncio.sleep(random.uniform(0.01, 0.03))

            # Mock inventory check - randomly fail 5% of the time
            if random.random() < 0.05:
                span.set_attribute("inventory.available", False)
                span.set_attribute("inventory.error", "out_of_stock")
                raise ValueError("Some items are out of stock")

            span.set_attribute("inventory.available", True)
            for item in items:
                span.set_attribute(f"inventory.{item}", "available")

    async def _calculate_total(self, order_data: Dict[str, Any]) -> float:
        """Calculate order total with tracing."""
        with tracer.start_as_current_span("order_service.calculate_total") as span:
            span.set_attribute("service", "order")
            span.set_attribute("operation", "calculate_total")

            # Simulate pricing service call
            await asyncio.sleep(random.uniform(0.005, 0.02))

            base_amount = order_data.get("amount", 0.0)
            tax_rate = 0.08  # 8% tax

            tax = base_amount * tax_rate
            total = base_amount + tax

            span.set_attribute("calculation.base_amount", base_amount)
            span.set_attribute("calculation.tax_rate", tax_rate)
            span.set_attribute("calculation.tax", tax)
            span.set_attribute("calculation.total", total)

            return total

    async def _send_order_notification(self, order: Dict[str, Any]) -> None:
        """Send order notification with tracing."""
        with tracer.start_as_current_span("order_service.send_notification") as span:
            span.set_attribute("service", "order")
            span.set_attribute("operation", "send_notification")
            span.set_attribute("notification.order_id", order["id"])
            span.set_attribute("notification.user_id", order["user_id"])

            # Simulate notification service call
            await asyncio.sleep(random.uniform(0.01, 0.03))

            # Mock notification - randomly fail 2% of the time
            if random.random() < 0.02:
                span.set_attribute("notification.success", False)
                span.set_attribute("notification.error", "delivery_failed")
                # Don't raise error for notification failures - just log
                return

            span.set_attribute("notification.success", True)
            span.set_attribute("notification.type", "email")

    async def update_order_status(self, order_id: int, status: str) -> Dict[str, Any]:
        """Update order status with tracing."""
        with tracer.start_as_current_span("order_service.update_status") as span:
            span.set_attribute("service", "order")
            span.set_attribute("operation", "update_status")
            span.set_attribute("order_id", order_id)
            span.set_attribute("new_status", status)

            # Simulate database update delay
            await asyncio.sleep(random.uniform(0.01, 0.04))

            if order_id not in self.orders:
                span.set_attribute("order.found", False)
                raise ValueError(f"Order {order_id} not found")

            old_status = self.orders[order_id]["status"]
            self.orders[order_id]["status"] = status

            span.set_attribute("order.old_status", old_status)
            span.set_attribute("order.updated", True)

            return self.orders[order_id]
