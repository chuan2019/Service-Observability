"""
Shared Pydantic models for microservices communication.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class OrderStatus(str, Enum):
    """Order status enumeration."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class NotificationStatus(str, Enum):
    """Notification status enumeration."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


# User Service Models
class UserBase(BaseModel):
    """Base user model."""

    email: EmailStr
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    active: bool = True


class UserCreate(UserBase):
    """User creation model."""

    pass


class UserUpdate(BaseModel):
    """User update model."""

    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    active: Optional[bool] = None


class UserResponse(UserBase):
    """User response model."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Product Service Models
class ProductBase(BaseModel):
    """Base product model."""

    name: str
    description: Optional[str] = None
    price: float
    category: str
    sku: str
    active: bool = True


class ProductCreate(ProductBase):
    """Product creation model."""

    pass


class ProductUpdate(BaseModel):
    """Product update model."""

    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    active: Optional[bool] = None


class ProductResponse(ProductBase):
    """Product response model."""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Inventory Service Models
class StockBase(BaseModel):
    """Base stock model."""

    product_id: int
    available_quantity: int
    reserved_quantity: int = 0
    reorder_level: int = 10


class StockCreate(StockBase):
    """Stock creation model."""

    pass


class StockUpdate(BaseModel):
    """Stock update model."""

    available_quantity: Optional[int] = None
    reserved_quantity: Optional[int] = None
    reorder_level: Optional[int] = None


class StockResponse(StockBase):
    """Stock response model."""

    id: int
    last_updated: datetime

    class Config:
        from_attributes = True


class StockReservationRequest(BaseModel):
    """Stock reservation request model."""

    product_id: int
    quantity: int
    order_id: int


class StockReservationResponse(BaseModel):
    """Stock reservation response model."""

    id: int
    stock_id: int
    order_id: int
    quantity: int
    reserved_at: datetime

    class Config:
        from_attributes = True


# Order Service Models
class OrderItemBase(BaseModel):
    """Base order item model."""

    product_id: int
    quantity: int
    unit_price: float


class OrderItemCreate(OrderItemBase):
    """Order item creation model."""

    pass


class OrderItemResponse(OrderItemBase):
    """Order item response model."""

    id: int
    total_price: float

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    """Base order model."""

    user_id: int
    status: OrderStatus = OrderStatus.PENDING


class OrderCreate(BaseModel):
    """Order creation model."""

    user_id: int
    items: List[OrderItemCreate]


class OrderResponse(OrderBase):
    """Order response model."""

    id: int
    items: List[OrderItemResponse] = []
    total_amount: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Payment Service Models
class PaymentBase(BaseModel):
    """Base payment model."""

    order_id: int
    amount: float
    payment_method: str
    status: PaymentStatus = PaymentStatus.PENDING


class PaymentCreate(PaymentBase):
    """Payment creation model."""

    pass


class PaymentResponse(PaymentBase):
    """Payment response model."""

    id: int
    transaction_id: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Notification Service Models
class NotificationBase(BaseModel):
    """Base notification model."""

    user_id: int
    order_id: Optional[int] = None
    type: str
    subject: str
    message: str
    status: NotificationStatus = NotificationStatus.PENDING


class NotificationCreate(NotificationBase):
    """Notification creation model."""

    pass


class NotificationResponse(NotificationBase):
    """Notification response model."""

    id: int
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Health Check Models
class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    service: str
    timestamp: datetime
    version: str = "1.0.0"
