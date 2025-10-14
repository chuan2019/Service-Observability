"""Order service with Prometheus metrics."""

import asyncio
import random
from typing import Any, Dict, List

from prometheus_client import Counter, Histogram, Gauge
from app.middleware.metrics import REGISTRY

# Order service specific metrics
ORDER_OPERATIONS = Counter(
    'order_service_operations_total',
    'Total order service operations',
    ['operation', 'status'],
    registry=REGISTRY
)

ORDER_OPERATION_DURATION = Histogram(
    'order_service_operation_duration_seconds',
    'Order service operation duration',
    ['operation'],
    registry=REGISTRY
)

ACTIVE_ORDERS = Gauge(
    'order_service_active_orders',
    'Number of active orders',
    registry=REGISTRY
)

ORDER_VALUE = Histogram(
    'order_service_order_value',
    'Order value distribution',
    ['order_type'],
    registry=REGISTRY
)

ORDER_ITEMS_COUNT = Histogram(
    'order_service_items_per_order',
    'Number of items per order',
    registry=REGISTRY
)

ORDER_STATUS_CHANGES = Counter(
    'order_service_status_changes_total',
    'Total order status changes',
    ['from_status', 'to_status'],
    registry=REGISTRY
)


class OrderService:
    """Service for managing orders with Prometheus metrics."""

    def __init__(self):
        self.orders: Dict[int, Dict[str, Any]] = {
            101: {
                "id": 101,
                "user_id": 1,
                "amount": 29.99,
                "items": ["item1", "item2"],
                "status": "completed",
                "type": "standard",
                "created_at": "2024-01-15T09:00:00Z",
            },
            102: {
                "id": 102,
                "user_id": 2,
                "amount": 49.99,
                "items": ["item3"],
                "status": "pending",
                "type": "express",
                "created_at": "2024-01-15T10:00:00Z",
            },
        }
        self.next_id = 103
        self._update_active_orders_count()

    def _update_active_orders_count(self):
        """Update the active orders gauge."""
        active_count = sum(1 for order in self.orders.values() 
                          if order.get("status") in ["pending", "processing"])
        ACTIVE_ORDERS.set(active_count)

    async def get_order(self, order_id: int) -> Dict[str, Any]:
        """Get order by ID with metrics."""
        with ORDER_OPERATION_DURATION.labels(operation="get_order").time():
            try:
                # Simulate database lookup delay
                await asyncio.sleep(random.uniform(0.01, 0.05))

                if order_id not in self.orders:
                    ORDER_OPERATIONS.labels(operation="get_order", status="not_found").inc()
                    raise ValueError(f"Order {order_id} not found")

                order = self.orders[order_id].copy()
                ORDER_OPERATIONS.labels(operation="get_order", status="success").inc()
                
                return order

            except Exception as e:
                ORDER_OPERATIONS.labels(operation="get_order", status="error").inc()
                raise e

    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order with metrics and cross-service validation."""
        with ORDER_OPERATION_DURATION.labels(operation="create_order").time():
            try:
                # Validate required fields
                required_fields = ["user_id", "amount", "items"]
                for field in required_fields:
                    if field not in order_data:
                        ORDER_OPERATIONS.labels(operation="create_order", status="validation_error").inc()
                        raise ValueError(f"Missing required field: {field}")

                # Validate user exists (cross-service call)
                from app.services.user_service import UserService
                user_service = UserService()
                user_exists = await user_service.validate_user_exists(order_data["user_id"])
                
                if not user_exists:
                    ORDER_OPERATIONS.labels(operation="create_order", status="user_not_found").inc()
                    raise ValueError(f"User {order_data['user_id']} does not exist")

                # Simulate order creation delay
                await asyncio.sleep(random.uniform(0.05, 0.15))

                # Create new order
                order_id = self.next_id
                self.next_id += 1

                order_type = order_data.get("type", "standard")
                
                order = {
                    "id": order_id,
                    "user_id": order_data["user_id"],
                    "amount": float(order_data["amount"]),
                    "items": order_data["items"],
                    "status": "pending",
                    "type": order_type,
                    "created_at": "2024-01-15T10:30:00Z",
                    "estimated_delivery": "2024-01-18T10:30:00Z",
                }

                self.orders[order_id] = order
                self._update_active_orders_count()

                # Record metrics
                ORDER_VALUE.labels(order_type=order_type).observe(order["amount"])
                ORDER_ITEMS_COUNT.observe(len(order["items"]))
                ORDER_STATUS_CHANGES.labels(from_status="none", to_status="pending").inc()
                ORDER_OPERATIONS.labels(operation="create_order", status="success").inc()

                # Simulate inventory check (might fail sometimes)
                if random.random() < 0.1:  # 10% chance of inventory failure
                    await self._update_order_status(order_id, "cancelled", "inventory_unavailable")
                    ORDER_OPERATIONS.labels(operation="create_order", status="inventory_failed").inc()
                    raise ValueError("Items not available in inventory")

                return order.copy()

            except Exception as e:
                ORDER_OPERATIONS.labels(operation="create_order", status="error").inc()
                raise e

    async def update_order_status(self, order_id: int, new_status: str, reason: str = None) -> Dict[str, Any]:
        """Update order status with metrics."""
        return await self._update_order_status(order_id, new_status, reason)

    async def _update_order_status(self, order_id: int, new_status: str, reason: str = None) -> Dict[str, Any]:
        """Internal method to update order status."""
        with ORDER_OPERATION_DURATION.labels(operation="update_status").time():
            try:
                # Simulate database update delay
                await asyncio.sleep(random.uniform(0.02, 0.06))

                if order_id not in self.orders:
                    ORDER_OPERATIONS.labels(operation="update_status", status="not_found").inc()
                    raise ValueError(f"Order {order_id} not found")

                order = self.orders[order_id]
                old_status = order["status"]
                
                # Update status
                order["status"] = new_status
                order["updated_at"] = "2024-01-15T10:30:00Z"
                if reason:
                    order["status_reason"] = reason

                self._update_active_orders_count()

                # Record status change metric
                ORDER_STATUS_CHANGES.labels(from_status=old_status, to_status=new_status).inc()
                ORDER_OPERATIONS.labels(operation="update_status", status="success").inc()

                return order.copy()

            except Exception as e:
                ORDER_OPERATIONS.labels(operation="update_status", status="error").inc()
                raise e

    async def get_orders_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all orders for a user with metrics."""
        with ORDER_OPERATION_DURATION.labels(operation="get_orders_by_user").time():
            try:
                # Simulate database query delay
                await asyncio.sleep(random.uniform(0.03, 0.08))

                orders = [order.copy() for order in self.orders.values() 
                         if order["user_id"] == user_id]
                
                ORDER_OPERATIONS.labels(operation="get_orders_by_user", status="success").inc()
                return orders

            except Exception as e:
                ORDER_OPERATIONS.labels(operation="get_orders_by_user", status="error").inc()
                raise e

    async def get_all_orders(self) -> List[Dict[str, Any]]:
        """Get all orders with metrics."""
        with ORDER_OPERATION_DURATION.labels(operation="get_all_orders").time():
            try:
                # Simulate database query delay
                await asyncio.sleep(random.uniform(0.05, 0.12))

                orders = [order.copy() for order in self.orders.values()]
                ORDER_OPERATIONS.labels(operation="get_all_orders", status="success").inc()
                
                return orders

            except Exception as e:
                ORDER_OPERATIONS.labels(operation="get_all_orders", status="error").inc()
                raise e

    async def process_order(self, order_id: int) -> Dict[str, Any]:
        """Process an order (move from pending to processing) with metrics."""
        with ORDER_OPERATION_DURATION.labels(operation="process_order").time():
            try:
                if order_id not in self.orders:
                    ORDER_OPERATIONS.labels(operation="process_order", status="not_found").inc()
                    raise ValueError(f"Order {order_id} not found")

                order = self.orders[order_id]
                
                if order["status"] != "pending":
                    ORDER_OPERATIONS.labels(operation="process_order", status="invalid_status").inc()
                    raise ValueError(f"Order {order_id} cannot be processed from status: {order['status']}")

                # Simulate order processing
                await asyncio.sleep(random.uniform(0.1, 0.3))

                # Update to processing status
                await self._update_order_status(order_id, "processing", "order_being_processed")

                ORDER_OPERATIONS.labels(operation="process_order", status="success").inc()
                return self.orders[order_id].copy()

            except Exception as e:
                ORDER_OPERATIONS.labels(operation="process_order", status="error").inc()
                raise e

    async def cancel_order(self, order_id: int, reason: str = "user_requested") -> Dict[str, Any]:
        """Cancel an order with metrics."""
        with ORDER_OPERATION_DURATION.labels(operation="cancel_order").time():
            try:
                if order_id not in self.orders:
                    ORDER_OPERATIONS.labels(operation="cancel_order", status="not_found").inc()
                    raise ValueError(f"Order {order_id} not found")

                order = self.orders[order_id]
                
                if order["status"] in ["completed", "cancelled"]:
                    ORDER_OPERATIONS.labels(operation="cancel_order", status="invalid_status").inc()
                    raise ValueError(f"Order {order_id} cannot be cancelled from status: {order['status']}")

                # Simulate cancellation processing
                await asyncio.sleep(random.uniform(0.02, 0.08))

                # Update to cancelled status
                await self._update_order_status(order_id, "cancelled", reason)

                ORDER_OPERATIONS.labels(operation="cancel_order", status="success").inc()
                return self.orders[order_id].copy()

            except Exception as e:
                ORDER_OPERATIONS.labels(operation="cancel_order", status="error").inc()
                raise e