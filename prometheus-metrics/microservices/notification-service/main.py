"""Notification microservice main application."""

import os
import random
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import REGISTRY, Counter, Gauge, Histogram, make_asgi_app
from shared.config import NotificationServiceSettings
from shared.database import get_db_manager, init_db_manager
from shared.middleware import PrometheusMiddleware
from shared.models import Notification
from shared.schemas import HealthResponse, NotificationCreate, NotificationResponse, NotificationStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Metrics
NOTIFICATION_OPERATIONS = Counter(
    "notification_service_operations_total",
    "Total notification service operations",
    ["operation", "type", "status"],
    registry=REGISTRY,
)

NOTIFICATION_OPERATION_DURATION = Histogram(
    "notification_service_operation_duration_seconds",
    "Notification service operation duration",
    ["operation"],
    registry=REGISTRY,
)

PENDING_NOTIFICATIONS = Gauge(
    "notification_service_pending_notifications",
    "Number of pending notifications",
    registry=REGISTRY,
)

settings = NotificationServiceSettings()


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
app.add_middleware(PrometheusMiddleware, service_name="notification-service")

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


@app.post("/notifications", response_model=NotificationResponse)
async def send_notification(notification_data: NotificationCreate, session: AsyncSession = Depends(get_session)):
    """Send a notification."""
    with NOTIFICATION_OPERATION_DURATION.labels(operation="send").time():
        try:
            # Create notification record
            notification = Notification(
                user_id=notification_data.user_id,
                order_id=notification_data.order_id,
                type=notification_data.type,
                subject=notification_data.subject,
                message=notification_data.message,
                status=NotificationStatus.PENDING,
            )
            session.add(notification)
            await session.flush()

            # Simulate sending notification
            # In real world, this would call email/SMS service API
            success = random.random() > 0.05  # 95% success rate

            if success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                NOTIFICATION_OPERATIONS.labels(operation="send", type=notification_data.type, status="success").inc()
            else:
                notification.status = NotificationStatus.FAILED
                NOTIFICATION_OPERATIONS.labels(operation="send", type=notification_data.type, status="failed").inc()

            await session.commit()
            await session.refresh(notification)

            # Update pending count
            pending_result = await session.execute(
                select(Notification).where(Notification.status == NotificationStatus.PENDING)
            )
            pending_count = len(pending_result.scalars().all())
            PENDING_NOTIFICATIONS.set(pending_count)

            return NotificationResponse.model_validate(notification)
        except Exception as e:
            await session.rollback()
            NOTIFICATION_OPERATIONS.labels(operation="send", type=notification_data.type, status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications", response_model=List[NotificationResponse])
async def list_notifications(skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_session)):
    """Get all notifications."""
    with NOTIFICATION_OPERATION_DURATION.labels(operation="list").time():
        try:
            result = await session.execute(select(Notification).offset(skip).limit(limit))
            notifications = result.scalars().all()

            NOTIFICATION_OPERATIONS.labels(operation="list", type="all", status="success").inc()
            return [NotificationResponse.model_validate(notif) for notif in notifications]
        except Exception as e:
            NOTIFICATION_OPERATIONS.labels(operation="list", type="all", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications/{notification_id}", response_model=NotificationResponse)
async def get_notification(notification_id: int, session: AsyncSession = Depends(get_session)):
    """Get notification by ID."""
    with NOTIFICATION_OPERATION_DURATION.labels(operation="get").time():
        try:
            result = await session.execute(select(Notification).where(Notification.id == notification_id))
            notification = result.scalar_one_or_none()

            if not notification:
                NOTIFICATION_OPERATIONS.labels(operation="get", type="single", status="error").inc()
                raise HTTPException(status_code=404, detail="Notification not found")

            NOTIFICATION_OPERATIONS.labels(operation="get", type="single", status="success").inc()
            return NotificationResponse.model_validate(notification)
        except HTTPException:
            raise
        except Exception as e:
            NOTIFICATION_OPERATIONS.labels(operation="get", type="single", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications/user/{user_id}", response_model=List[NotificationResponse])
async def get_user_notifications(user_id: int, session: AsyncSession = Depends(get_session)):
    """Get all notifications for a user."""
    with NOTIFICATION_OPERATION_DURATION.labels(operation="get_user_notifications").time():
        try:
            result = await session.execute(select(Notification).where(Notification.user_id == user_id))
            notifications = result.scalars().all()

            NOTIFICATION_OPERATIONS.labels(operation="get_user_notifications", type="user", status="success").inc()
            return [NotificationResponse.model_validate(notif) for notif in notifications]
        except Exception as e:
            NOTIFICATION_OPERATIONS.labels(operation="get_user_notifications", type="user", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications/order/{order_id}", response_model=List[NotificationResponse])
async def get_order_notifications(order_id: int, session: AsyncSession = Depends(get_session)):
    """Get all notifications for an order."""
    with NOTIFICATION_OPERATION_DURATION.labels(operation="get_order_notifications").time():
        try:
            result = await session.execute(select(Notification).where(Notification.order_id == order_id))
            notifications = result.scalars().all()

            NOTIFICATION_OPERATIONS.labels(operation="get_order_notifications", type="order", status="success").inc()
            return [NotificationResponse.model_validate(notif) for notif in notifications]
        except Exception as e:
            NOTIFICATION_OPERATIONS.labels(operation="get_order_notifications", type="order", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/notifications/{notification_id}/retry")
async def retry_notification(notification_id: int, session: AsyncSession = Depends(get_session)):
    """Retry a failed notification."""
    with NOTIFICATION_OPERATION_DURATION.labels(operation="retry").time():
        try:
            result = await session.execute(select(Notification).where(Notification.id == notification_id))
            notification = result.scalar_one_or_none()

            if not notification:
                NOTIFICATION_OPERATIONS.labels(operation="retry", type="retry", status="error").inc()
                raise HTTPException(status_code=404, detail="Notification not found")

            if notification.status != NotificationStatus.FAILED:
                raise HTTPException(status_code=400, detail="Can only retry failed notifications")

            # Simulate retry
            success = random.random() > 0.05

            if success:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                NOTIFICATION_OPERATIONS.labels(operation="retry", type=notification.type, status="success").inc()
            else:
                NOTIFICATION_OPERATIONS.labels(operation="retry", type=notification.type, status="failed").inc()

            notification.updated_at = datetime.utcnow()
            await session.commit()

            return {"status": notification.status.value, "notification_id": notification_id}
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            NOTIFICATION_OPERATIONS.labels(operation="retry", type="unknown", status="error").inc()
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
