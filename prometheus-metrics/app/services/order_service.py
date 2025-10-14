"""Order service that orchestrates the complete order workflow with database operations and Prometheus metrics."""

import httpx
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from prometheus_client import Counter, Histogram, Gauge

from app.middleware.metrics import REGISTRY
from app.models import Order, OrderItem, Product, User, OrderStatus
from app.services.user_service import user_service
from app.services.product_service import product_service
from app.services.inventory_service import inventory_service
from app.services.payment_service import payment_service
from app.services.notification_service import notification_service

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

ORDER_VALUE = Histogram(
    'order_service_value',
    'Order values',
    ['status'],
    registry=REGISTRY
)

ORDER_ITEMS_COUNT = Histogram(
    'order_service_items_count',
    'Number of items per order',
    registry=REGISTRY
)

ORDER_STATUS_CHANGES = Counter(
    'order_service_status_changes_total',
    'Total order status changes',
    ['from_status', 'to_status'],
    registry=REGISTRY
)

ACTIVE_ORDERS = Gauge(
    'order_service_active_orders',
    'Number of active orders',
    ['status'],
    registry=REGISTRY
)

ORDER_DATABASE_QUERIES = Counter(
    'order_service_db_queries_total',
    'Total database queries in order service',
    ['query_type', 'status'],
    registry=REGISTRY
)

WORKFLOW_STEPS = Counter(
    'order_service_workflow_steps_total',
    'Total workflow steps executed',
    ['step', 'status'],
    registry=REGISTRY
)


class OrderService:
    """Service for managing orders and orchestrating the complete order workflow."""

    def __init__(self):
        """Initialize the order service."""
        pass

    async def create_order(self, session: AsyncSession, order_data: Dict[str, Any]) -> Order:
        """Create a new order with complete workflow orchestration."""
        with ORDER_OPERATION_DURATION.labels(operation="create_order").time():
            try:
                # Step 1: Validate user exists
                WORKFLOW_STEPS.labels(step="validate_user", status="started").inc()
                user = await user_service.get_user_by_id(session, order_data["user_id"])
                if not user:
                    WORKFLOW_STEPS.labels(step="validate_user", status="failed").inc()
                    ORDER_OPERATIONS.labels(operation="create_order", status="user_not_found").inc()
                    raise ValueError(f"User {order_data['user_id']} not found")
                WORKFLOW_STEPS.labels(step="validate_user", status="success").inc()

                # Step 2: Validate products and calculate total
                WORKFLOW_STEPS.labels(step="validate_products", status="started").inc()
                order_items = []
                total_amount = 0.0
                
                for item_data in order_data["items"]:
                    product = await product_service.get_product_by_id(session, item_data["product_id"])
                    if not product:
                        WORKFLOW_STEPS.labels(step="validate_products", status="failed").inc()
                        ORDER_OPERATIONS.labels(operation="create_order", status="product_not_found").inc()
                        raise ValueError(f"Product {item_data['product_id']} not found")
                    
                    quantity = item_data["quantity"]
                    unit_price = product.price
                    total_price = unit_price * quantity
                    total_amount += total_price
                    
                    order_items.append({
                        "product_id": product.id,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "total_price": total_price
                    })
                
                WORKFLOW_STEPS.labels(step="validate_products", status="success").inc()

                # Step 3: Create order record
                WORKFLOW_STEPS.labels(step="create_order_record", status="started").inc()
                ORDER_DATABASE_QUERIES.labels(query_type="insert", status="started").inc()
                
                order = Order(
                    user_id=order_data["user_id"],
                    total_amount=total_amount,
                    status=OrderStatus.PENDING,
                    shipping_address=order_data.get("shipping_address", user.address),
                    notes=order_data.get("notes")
                )
                
                session.add(order)
                await session.commit()
                await session.refresh(order)
                
                # Add order items
                for item_data in order_items:
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=item_data["product_id"],
                        quantity=item_data["quantity"],
                        unit_price=item_data["unit_price"],
                        total_price=item_data["total_price"]
                    )
                    session.add(order_item)
                
                await session.commit()
                
                ORDER_DATABASE_QUERIES.labels(query_type="insert", status="success").inc()
                WORKFLOW_STEPS.labels(step="create_order_record", status="success").inc()

                # Step 4: Reserve inventory
                WORKFLOW_STEPS.labels(step="reserve_inventory", status="started").inc()
                try:
                    for item_data in order_items:
                        reserved = await inventory_service.reserve_stock(
                            session, 
                            item_data["product_id"], 
                            item_data["quantity"], 
                            order.id
                        )
                        if not reserved:
                            raise ValueError(f"Insufficient inventory for product {item_data['product_id']}")
                    
                    WORKFLOW_STEPS.labels(step="reserve_inventory", status="success").inc()
                    
                except Exception as e:
                    WORKFLOW_STEPS.labels(step="reserve_inventory", status="failed").inc()
                    # Rollback order creation
                    await self._cancel_order_internal(session, order.id, "inventory_reservation_failed")
                    raise ValueError(f"Failed to reserve inventory: {str(e)}")

                # Record metrics
                ORDER_OPERATIONS.labels(operation="create_order", status="success").inc()
                ORDER_VALUE.labels(status="created").observe(total_amount)
                ORDER_ITEMS_COUNT.observe(len(order_items))
                
                # Update active orders gauge
                await self._update_active_orders_count(session)
                
                # Send order confirmation notification (async, don't wait)
                try:
                    await notification_service.send_order_confirmation(session, order.id)
                except Exception:
                    # Don't fail order creation if notification fails
                    pass

                return order
                
            except Exception as e:
                await session.rollback()
                ORDER_DATABASE_QUERIES.labels(query_type="insert", status="error").inc()
                ORDER_OPERATIONS.labels(operation="create_order", status="error").inc()
                raise

    async def process_order_payment(self, session: AsyncSession, order_id: int, payment_data: Dict[str, Any]) -> Order:
        """Process payment for an order and update status."""
        with ORDER_OPERATION_DURATION.labels(operation="process_payment").time():
            try:
                # Get the order
                order = await self.get_order_by_id(session, order_id)
                if not order:
                    ORDER_OPERATIONS.labels(operation="process_payment", status="order_not_found").inc()
                    raise ValueError(f"Order {order_id} not found")

                if order.status != OrderStatus.PENDING:
                    ORDER_OPERATIONS.labels(operation="process_payment", status="invalid_status").inc()
                    raise ValueError(f"Order {order_id} is not in pending status")

                # Process payment
                WORKFLOW_STEPS.labels(step="process_payment", status="started").inc()
                payment = await payment_service.process_payment(session, {
                    "order_id": order_id,
                    "amount": payment_data["amount"],
                    "method": payment_data["method"]
                })

                if payment.status.value == "completed":
                    # Payment successful - update order status
                    await self._update_order_status(session, order_id, OrderStatus.CONFIRMED)
                    
                    # Confirm inventory reservations
                    await inventory_service.confirm_reservation(session, order_id)
                    
                    WORKFLOW_STEPS.labels(step="process_payment", status="success").inc()
                    ORDER_OPERATIONS.labels(operation="process_payment", status="success").inc()
                    
                    # Send payment confirmation notification
                    try:
                        await notification_service.send_payment_confirmation(session, order_id, payment.amount)
                    except Exception:
                        pass
                        
                else:
                    # Payment failed - release inventory and cancel order
                    await inventory_service.release_reservation(session, order_id)
                    await self._update_order_status(session, order_id, OrderStatus.CANCELLED)
                    
                    WORKFLOW_STEPS.labels(step="process_payment", status="failed").inc()
                    ORDER_OPERATIONS.labels(operation="process_payment", status="payment_failed").inc()

                # Get updated order
                updated_order = await self.get_order_by_id(session, order_id)
                return updated_order

            except Exception as e:
                ORDER_OPERATIONS.labels(operation="process_payment", status="error").inc()
                raise

    async def cancel_order(self, session: AsyncSession, order_id: int, reason: str = "customer_request") -> bool:
        """Cancel an order and handle cleanup."""
        with ORDER_OPERATION_DURATION.labels(operation="cancel_order").time():
            try:
                result = await self._cancel_order_internal(session, order_id, reason)
                if result:
                    ORDER_OPERATIONS.labels(operation="cancel_order", status="success").inc()
                else:
                    ORDER_OPERATIONS.labels(operation="cancel_order", status="not_found").inc()
                return result
                
            except Exception as e:
                ORDER_OPERATIONS.labels(operation="cancel_order", status="error").inc()
                raise

    async def get_order_by_id(self, session: AsyncSession, order_id: int) -> Optional[Order]:
        """Get an order by ID with all related data."""
        with ORDER_OPERATION_DURATION.labels(operation="get_by_id").time():
            try:
                ORDER_DATABASE_QUERIES.labels(query_type="select", status="started").inc()
                
                result = await session.execute(
                    select(Order)
                    .options(selectinload(Order.items), selectinload(Order.user))
                    .where(Order.id == order_id)
                )
                order = result.scalar_one_or_none()
                
                ORDER_DATABASE_QUERIES.labels(query_type="select", status="success").inc()
                
                if order:
                    ORDER_OPERATIONS.labels(operation="get_by_id", status="success").inc()
                else:
                    ORDER_OPERATIONS.labels(operation="get_by_id", status="not_found").inc()
                
                return order
                
            except Exception as e:
                ORDER_DATABASE_QUERIES.labels(query_type="select", status="error").inc()
                ORDER_OPERATIONS.labels(operation="get_by_id", status="error").inc()
                raise

    async def get_orders_by_user(self, session: AsyncSession, user_id: int, skip: int = 0, limit: int = 50) -> List[Order]:
        """Get all orders for a user."""
        with ORDER_OPERATION_DURATION.labels(operation="get_by_user").time():
            try:
                ORDER_DATABASE_QUERIES.labels(query_type="select", status="started").inc()
                
                result = await session.execute(
                    select(Order)
                    .options(selectinload(Order.items))
                    .where(Order.user_id == user_id)
                    .offset(skip)
                    .limit(limit)
                    .order_by(Order.created_at.desc())
                )
                orders = result.scalars().all()
                
                ORDER_DATABASE_QUERIES.labels(query_type="select", status="success").inc()
                ORDER_OPERATIONS.labels(operation="get_by_user", status="success").inc()
                
                return list(orders)
                
            except Exception as e:
                ORDER_DATABASE_QUERIES.labels(query_type="select", status="error").inc()
                ORDER_OPERATIONS.labels(operation="get_by_user", status="error").inc()
                raise

    async def _update_order_status(self, session: AsyncSession, order_id: int, new_status: OrderStatus) -> None:
        """Update order status and record metrics."""
        order = await self.get_order_by_id(session, order_id)
        if order:
            old_status = order.status
            order.status = new_status
            order.updated_at = datetime.utcnow()
            
            await session.commit()
            
            # Record status change metric
            ORDER_STATUS_CHANGES.labels(from_status=old_status.value, to_status=new_status.value).inc()
            
            # Update active orders count
            await self._update_active_orders_count(session)
            
            # Send status update notification
            try:
                await notification_service.send_order_status_update(session, order_id, new_status.value)
            except Exception:
                pass

    async def _cancel_order_internal(self, session: AsyncSession, order_id: int, reason: str) -> bool:
        """Internal method to cancel order and cleanup resources."""
        order = await self.get_order_by_id(session, order_id)
        if not order:
            return False
        
        # Release inventory reservations
        await inventory_service.release_reservation(session, order_id)
        
        # Update order status
        await self._update_order_status(session, order_id, OrderStatus.CANCELLED)
        
        return True

    async def _update_active_orders_count(self, session: AsyncSession) -> None:
        """Update the active orders gauge metrics."""
        try:
            for status in OrderStatus:
                result = await session.execute(
                    select(Order.id).where(Order.status == status)
                )
                count = len(result.scalars().all())
                ACTIVE_ORDERS.labels(status=status.value).set(count)
        except Exception:
            # Don't fail the main operation if metrics update fails
            pass

# Global service instance
order_service = OrderService()