"""Notification service with database operations and Prometheus metrics."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from prometheus_client import Counter, Histogram, Gauge
import asyncio
import random

from app.middleware.metrics import REGISTRY
from app.models import Notification, User, Order, NotificationStatus

# Notification service specific metrics
NOTIFICATION_OPERATIONS = Counter(
    'notification_service_operations_total',
    'Total notification service operations',
    ['operation', 'status'],
    registry=REGISTRY
)

NOTIFICATION_OPERATION_DURATION = Histogram(
    'notification_service_operation_duration_seconds',
    'Notification service operation duration',
    ['operation'],
    registry=REGISTRY
)

NOTIFICATIONS_SENT = Counter(
    'notification_service_sent_total',
    'Total notifications sent',
    ['type', 'status'],
    registry=REGISTRY
)

NOTIFICATION_QUEUE_SIZE = Gauge(
    'notification_service_queue_size',
    'Current notification queue size',
    registry=REGISTRY
)

NOTIFICATION_DATABASE_QUERIES = Counter(
    'notification_service_db_queries_total',
    'Total database queries in notification service',
    ['query_type', 'status'],
    registry=REGISTRY
)


class NotificationService:
    """Service for managing notifications with database operations and Prometheus metrics."""

    def __init__(self):
        """Initialize the notification service."""
        pass

    async def send_order_confirmation(self, session: AsyncSession, order_id: int) -> Notification:
        """Send order confirmation notification."""
        with NOTIFICATION_OPERATION_DURATION.labels(operation="order_confirmation").time():
            try:
                # Get order and user information
                order_result = await session.execute(
                    select(Order, User)
                    .join(User, Order.user_id == User.id)
                    .where(Order.id == order_id)
                )
                order_user = order_result.first()
                
                if not order_user:
                    NOTIFICATION_OPERATIONS.labels(operation="order_confirmation", status="order_not_found").inc()
                    raise ValueError(f"Order {order_id} not found")
                
                order, user = order_user
                
                # Create notification
                notification = await self._create_notification(
                    session=session,
                    user_id=user.id,
                    order_id=order_id,
                    notification_type="email",
                    subject=f"Order Confirmation #{order.id}",
                    message=f"Thank you {user.name}! Your order #{order.id} for ${order.total_amount:.2f} has been confirmed.",
                    recipient=user.email
                )
                
                # Simulate sending
                await self._simulate_email_send(notification)
                
                # Update notification status
                await self._update_notification_status(session, notification.id, NotificationStatus.SENT)
                
                NOTIFICATION_OPERATIONS.labels(operation="order_confirmation", status="success").inc()
                NOTIFICATIONS_SENT.labels(type="email", status="success").inc()
                
                return notification
                
            except Exception as e:
                NOTIFICATION_OPERATIONS.labels(operation="order_confirmation", status="error").inc()
                NOTIFICATIONS_SENT.labels(type="email", status="error").inc()
                raise

    async def send_order_status_update(self, session: AsyncSession, order_id: int, new_status: str) -> Notification:
        """Send order status update notification."""
        with NOTIFICATION_OPERATION_DURATION.labels(operation="status_update").time():
            try:
                # Get order and user information
                order_result = await session.execute(
                    select(Order, User)
                    .join(User, Order.user_id == User.id)
                    .where(Order.id == order_id)
                )
                order_user = order_result.first()
                
                if not order_user:
                    NOTIFICATION_OPERATIONS.labels(operation="status_update", status="order_not_found").inc()
                    raise ValueError(f"Order {order_id} not found")
                
                order, user = order_user
                
                # Create status-specific message
                status_messages = {
                    "confirmed": f"Your order #{order.id} has been confirmed and is being prepared.",
                    "shipped": f"Great news! Your order #{order.id} has been shipped and is on its way.",
                    "delivered": f"Your order #{order.id} has been delivered. Thank you for your business!",
                    "cancelled": f"Your order #{order.id} has been cancelled. If you have questions, please contact support."
                }
                
                message = status_messages.get(new_status, f"Your order #{order.id} status has been updated to: {new_status}")
                
                # Create notification
                notification = await self._create_notification(
                    session=session,
                    user_id=user.id,
                    order_id=order_id,
                    notification_type="email",
                    subject=f"Order Update #{order.id} - {new_status.title()}",
                    message=f"Hi {user.name}, {message}",
                    recipient=user.email
                )
                
                # Simulate sending
                await self._simulate_email_send(notification)
                
                # Update notification status
                await self._update_notification_status(session, notification.id, NotificationStatus.SENT)
                
                NOTIFICATION_OPERATIONS.labels(operation="status_update", status="success").inc()
                NOTIFICATIONS_SENT.labels(type="email", status="success").inc()
                
                return notification
                
            except Exception as e:
                NOTIFICATION_OPERATIONS.labels(operation="status_update", status="error").inc()
                NOTIFICATIONS_SENT.labels(type="email", status="error").inc()
                raise

    async def send_payment_confirmation(self, session: AsyncSession, order_id: int, payment_amount: float) -> Notification:
        """Send payment confirmation notification."""
        with NOTIFICATION_OPERATION_DURATION.labels(operation="payment_confirmation").time():
            try:
                # Get order and user information
                order_result = await session.execute(
                    select(Order, User)
                    .join(User, Order.user_id == User.id)
                    .where(Order.id == order_id)
                )
                order_user = order_result.first()
                
                if not order_user:
                    NOTIFICATION_OPERATIONS.labels(operation="payment_confirmation", status="order_not_found").inc()
                    raise ValueError(f"Order {order_id} not found")
                
                order, user = order_user
                
                # Create notification
                notification = await self._create_notification(
                    session=session,
                    user_id=user.id,
                    order_id=order_id,
                    notification_type="email",
                    subject=f"Payment Received - Order #{order.id}",
                    message=f"Hi {user.name}, we've successfully received your payment of ${payment_amount:.2f} for order #{order.id}. Your order is now being processed.",
                    recipient=user.email
                )
                
                # Simulate sending
                await self._simulate_email_send(notification)
                
                # Update notification status
                await self._update_notification_status(session, notification.id, NotificationStatus.SENT)
                
                NOTIFICATION_OPERATIONS.labels(operation="payment_confirmation", status="success").inc()
                NOTIFICATIONS_SENT.labels(type="email", status="success").inc()
                
                return notification
                
            except Exception as e:
                NOTIFICATION_OPERATIONS.labels(operation="payment_confirmation", status="error").inc()
                NOTIFICATIONS_SENT.labels(type="email", status="error").inc()
                raise

    async def _create_notification(self, session: AsyncSession, user_id: int, order_id: int, 
                                 notification_type: str, subject: str, message: str, recipient: str) -> Notification:
        """Create a notification record in the database."""
        NOTIFICATION_DATABASE_QUERIES.labels(query_type="insert", status="started").inc()
        
        notification = Notification(
            user_id=user_id,
            order_id=order_id,
            type=notification_type,
            subject=subject,
            message=message,
            recipient=recipient,
            status=NotificationStatus.PENDING
        )
        
        session.add(notification)
        await session.commit()
        await session.refresh(notification)
        
        NOTIFICATION_DATABASE_QUERIES.labels(query_type="insert", status="success").inc()
        
        # Update queue size metric
        await self._update_queue_size(session)
        
        return notification

    async def _update_notification_status(self, session: AsyncSession, notification_id: int, status: NotificationStatus) -> None:
        """Update notification status."""
        NOTIFICATION_DATABASE_QUERIES.labels(query_type="update", status="started").inc()
        
        result = await session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one()
        
        notification.status = status
        if status == NotificationStatus.SENT:
            notification.sent_at = datetime.utcnow()
        
        await session.commit()
        
        NOTIFICATION_DATABASE_QUERIES.labels(query_type="update", status="success").inc()
        
        # Update queue size metric
        await self._update_queue_size(session)

    async def _simulate_email_send(self, notification: Notification) -> None:
        """Simulate sending an email notification."""
        # Simulate email service delay
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # Simulate 95% success rate
        if random.random() > 0.05:
            # Success - notification will be marked as sent
            pass
        else:
            # Simulate failure
            raise Exception("Email service temporarily unavailable")

    async def _update_queue_size(self, session: AsyncSession) -> None:
        """Update the notification queue size metric."""
        try:
            result = await session.execute(
                select(Notification.id).where(Notification.status == NotificationStatus.PENDING)
            )
            count = len(result.scalars().all())
            NOTIFICATION_QUEUE_SIZE.set(count)
        except Exception:
            # Don't fail the main operation if metrics update fails
            pass

# Global service instance
notification_service = NotificationService()