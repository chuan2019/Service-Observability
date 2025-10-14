"""Inventory service with database operations and Prometheus metrics."""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from prometheus_client import Counter, Histogram, Gauge

from app.middleware.metrics import REGISTRY
from app.models import Stock, StockReservation, Product

# Inventory service specific metrics
INVENTORY_OPERATIONS = Counter(
    'inventory_service_operations_total',
    'Total inventory service operations',
    ['operation', 'status'],
    registry=REGISTRY
)

INVENTORY_OPERATION_DURATION = Histogram(
    'inventory_service_operation_duration_seconds',
    'Inventory service operation duration',
    ['operation'],
    registry=REGISTRY
)

STOCK_LEVELS = Gauge(
    'inventory_service_stock_levels',
    'Current stock levels by product',
    ['product_id'],
    registry=REGISTRY
)

STOCK_RESERVATIONS = Gauge(
    'inventory_service_reservations',
    'Current stock reservations',
    registry=REGISTRY
)

INVENTORY_DATABASE_QUERIES = Counter(
    'inventory_service_db_queries_total',
    'Total database queries in inventory service',
    ['query_type', 'status'],
    registry=REGISTRY
)

LOW_STOCK_ALERTS = Counter(
    'inventory_service_low_stock_alerts_total',
    'Total low stock alerts',
    ['product_id'],
    registry=REGISTRY
)


class InventoryService:
    """Service for managing inventory with database operations and Prometheus metrics."""

    def __init__(self):
        """Initialize the inventory service."""
        pass

    async def get_stock_by_product_id(self, session: AsyncSession, product_id: int) -> Optional[Stock]:
        """Get stock information for a product."""
        with INVENTORY_OPERATION_DURATION.labels(operation="get_stock").time():
            try:
                INVENTORY_DATABASE_QUERIES.labels(query_type="select", status="started").inc()
                
                result = await session.execute(
                    select(Stock).where(Stock.product_id == product_id)
                )
                stock = result.scalar_one_or_none()
                
                INVENTORY_DATABASE_QUERIES.labels(query_type="select", status="success").inc()
                
                if stock:
                    INVENTORY_OPERATIONS.labels(operation="get_stock", status="success").inc()
                    # Update stock level gauge
                    STOCK_LEVELS.labels(product_id=str(product_id)).set(stock.available_quantity)
                else:
                    INVENTORY_OPERATIONS.labels(operation="get_stock", status="not_found").inc()
                
                return stock
                
            except Exception as e:
                INVENTORY_DATABASE_QUERIES.labels(query_type="select", status="error").inc()
                INVENTORY_OPERATIONS.labels(operation="get_stock", status="error").inc()
                raise

    async def reserve_stock(self, session: AsyncSession, product_id: int, quantity: int, order_id: int, expires_minutes: int = 30) -> bool:
        """Reserve stock for an order."""
        with INVENTORY_OPERATION_DURATION.labels(operation="reserve_stock").time():
            try:
                # Get current stock
                stock = await self.get_stock_by_product_id(session, product_id)
                if not stock:
                    INVENTORY_OPERATIONS.labels(operation="reserve_stock", status="product_not_found").inc()
                    return False
                
                # Check if enough stock available
                if stock.available_quantity < quantity:
                    INVENTORY_OPERATIONS.labels(operation="reserve_stock", status="insufficient_stock").inc()
                    return False
                
                INVENTORY_DATABASE_QUERIES.labels(query_type="update", status="started").inc()
                
                # Update stock quantities
                stock.available_quantity -= quantity
                stock.reserved_quantity += quantity
                stock.last_updated = datetime.utcnow()
                
                # Create reservation record
                reservation = StockReservation(
                    stock_id=stock.id,
                    order_id=order_id,
                    quantity=quantity,
                    reserved_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(minutes=expires_minutes),
                    active=True
                )
                session.add(reservation)
                
                await session.commit()
                
                INVENTORY_DATABASE_QUERIES.labels(query_type="update", status="success").inc()
                INVENTORY_OPERATIONS.labels(operation="reserve_stock", status="success").inc()
                
                # Update metrics
                STOCK_LEVELS.labels(product_id=str(product_id)).set(stock.available_quantity)
                await self._update_reservations_count(session)
                
                return True
                
            except Exception as e:
                await session.rollback()
                INVENTORY_DATABASE_QUERIES.labels(query_type="update", status="error").inc()
                INVENTORY_OPERATIONS.labels(operation="reserve_stock", status="error").inc()
                raise

    async def release_reservation(self, session: AsyncSession, order_id: int) -> bool:
        """Release stock reservation for an order."""
        with INVENTORY_OPERATION_DURATION.labels(operation="release_reservation").time():
            try:
                INVENTORY_DATABASE_QUERIES.labels(query_type="select", status="started").inc()
                
                # Get active reservations for the order
                result = await session.execute(
                    select(StockReservation)
                    .where(StockReservation.order_id == order_id, StockReservation.active == True)
                )
                reservations = result.scalars().all()
                
                if not reservations:
                    INVENTORY_OPERATIONS.labels(operation="release_reservation", status="not_found").inc()
                    return False
                
                INVENTORY_DATABASE_QUERIES.labels(query_type="update", status="started").inc()
                
                # Release each reservation
                for reservation in reservations:
                    # Get the stock record
                    stock_result = await session.execute(
                        select(Stock).where(Stock.id == reservation.stock_id)
                    )
                    stock = stock_result.scalar_one()
                    
                    # Return quantity to available stock
                    stock.available_quantity += reservation.quantity
                    stock.reserved_quantity -= reservation.quantity
                    stock.last_updated = datetime.utcnow()
                    
                    # Mark reservation as inactive
                    reservation.active = False
                    
                    # Update stock level metric
                    STOCK_LEVELS.labels(product_id=str(stock.product_id)).set(stock.available_quantity)
                
                await session.commit()
                
                INVENTORY_DATABASE_QUERIES.labels(query_type="update", status="success").inc()
                INVENTORY_OPERATIONS.labels(operation="release_reservation", status="success").inc()
                
                # Update reservations count
                await self._update_reservations_count(session)
                
                return True
                
            except Exception as e:
                await session.rollback()
                INVENTORY_DATABASE_QUERIES.labels(query_type="update", status="error").inc()
                INVENTORY_OPERATIONS.labels(operation="release_reservation", status="error").inc()
                raise

    async def create_or_update_stock(self, session: AsyncSession, product_id: int, available_quantity: int, reorder_level: int = 10) -> Stock:
        """Create or update stock for a product."""
        with INVENTORY_OPERATION_DURATION.labels(operation="create_or_update_stock").time():
            try:
                # Check if stock already exists
                result = await session.execute(
                    select(Stock).where(Stock.product_id == product_id)
                )
                stock = result.scalar_one_or_none()
                
                if stock:
                    # Update existing stock
                    stock.available_quantity = available_quantity
                    stock.reorder_level = reorder_level
                    stock.updated_at = datetime.utcnow()
                    INVENTORY_DATABASE_QUERIES.labels(query_type="update", status="success").inc()
                else:
                    # Create new stock record
                    stock = Stock(
                        product_id=product_id,
                        available_quantity=available_quantity,
                        reserved_quantity=0,
                        reorder_level=reorder_level
                    )
                    session.add(stock)
                    INVENTORY_DATABASE_QUERIES.labels(query_type="insert", status="success").inc()
                
                await session.commit()
                
                # Update stock level metric
                STOCK_LEVELS.labels(product_id=str(product_id)).set(available_quantity)
                
                # Check for low stock
                if available_quantity <= reorder_level:
                    LOW_STOCK_ALERTS.inc()
                
                INVENTORY_OPERATIONS.labels(operation="create_or_update_stock", status="success").inc()
                
                return stock
                
            except Exception as e:
                await session.rollback()
                INVENTORY_DATABASE_QUERIES.labels(query_type="create_or_update", status="error").inc()
                INVENTORY_OPERATIONS.labels(operation="create_or_update_stock", status="error").inc()
                raise

    # Alias for backwards compatibility
    async def update_stock(self, session: AsyncSession, product_id: int, available_quantity: int, reorder_level: int = 10) -> Stock:
        """Alias for create_or_update_stock method."""
        return await self.create_or_update_stock(session, product_id, available_quantity, reorder_level)

    async def _update_reservations_count(self, session: AsyncSession) -> None:
        """Update the stock reservations gauge metric."""
        try:
            result = await session.execute(
                select(StockReservation.id).where(StockReservation.active == True)
            )
            count = len(result.scalars().all())
            STOCK_RESERVATIONS.set(count)
        except Exception:
            # Don't fail the main operation if metrics update fails
            pass

# Global service instance
inventory_service = InventoryService()