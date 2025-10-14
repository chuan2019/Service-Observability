"""Product service with database operations and Prometheus metrics."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from prometheus_client import Counter, Histogram, Gauge

from app.middleware.metrics import REGISTRY
from app.models import Product

# Product service specific metrics
PRODUCT_OPERATIONS = Counter(
    'product_service_operations_total',
    'Total product service operations',
    ['operation', 'status'],
    registry=REGISTRY
)

PRODUCT_OPERATION_DURATION = Histogram(
    'product_service_operation_duration_seconds',
    'Product service operation duration',
    ['operation'],
    registry=REGISTRY
)

ACTIVE_PRODUCTS = Gauge(
    'product_service_active_products',
    'Number of active products',
    registry=REGISTRY
)

PRODUCT_DATABASE_QUERIES = Counter(
    'product_service_db_queries_total',
    'Total database queries in product service',
    ['query_type', 'status'],
    registry=REGISTRY
)

PRODUCT_SEARCHES = Counter(
    'product_service_searches_total',
    'Total product searches',
    ['search_type'],
    registry=REGISTRY
)


class ProductService:
    """Service for managing products with database operations and Prometheus metrics."""

    def __init__(self):
        """Initialize the product service."""
        pass

    async def get_all_products(self, session: AsyncSession, skip: int = 0, limit: int = 100, category: str = None) -> List[Product]:
        """Get all products with optional category filter and pagination."""
        with PRODUCT_OPERATION_DURATION.labels(operation="get_all").time():
            try:
                PRODUCT_DATABASE_QUERIES.labels(query_type="select", status="started").inc()
                
                query = select(Product).where(Product.active == True)
                
                if category:
                    query = query.where(Product.category == category)
                    PRODUCT_SEARCHES.labels(search_type="category").inc()
                
                result = await session.execute(
                    query.offset(skip).limit(limit).order_by(Product.created_at.desc())
                )
                products = result.scalars().all()
                
                PRODUCT_DATABASE_QUERIES.labels(query_type="select", status="success").inc()
                PRODUCT_OPERATIONS.labels(operation="get_all", status="success").inc()
                
                # Update active products gauge
                await self._update_active_products_count(session)
                
                return list(products)
                
            except Exception as e:
                PRODUCT_DATABASE_QUERIES.labels(query_type="select", status="error").inc()
                PRODUCT_OPERATIONS.labels(operation="get_all", status="error").inc()
                raise

    async def get_product_by_id(self, session: AsyncSession, product_id: int) -> Optional[Product]:
        """Get a product by ID."""
        with PRODUCT_OPERATION_DURATION.labels(operation="get_by_id").time():
            try:
                PRODUCT_DATABASE_QUERIES.labels(query_type="select", status="started").inc()
                
                result = await session.execute(
                    select(Product).where(Product.id == product_id, Product.active == True)
                )
                product = result.scalar_one_or_none()
                
                PRODUCT_DATABASE_QUERIES.labels(query_type="select", status="success").inc()
                
                if product:
                    PRODUCT_OPERATIONS.labels(operation="get_by_id", status="success").inc()
                else:
                    PRODUCT_OPERATIONS.labels(operation="get_by_id", status="not_found").inc()
                
                return product
                
            except Exception as e:
                PRODUCT_DATABASE_QUERIES.labels(query_type="select", status="error").inc()
                PRODUCT_OPERATIONS.labels(operation="get_by_id", status="error").inc()
                raise

    async def get_product_by_sku(self, session: AsyncSession, sku: str) -> Optional[Product]:
        """Get a product by SKU."""
        with PRODUCT_OPERATION_DURATION.labels(operation="get_by_sku").time():
            try:
                PRODUCT_DATABASE_QUERIES.labels(query_type="select", status="started").inc()
                
                result = await session.execute(
                    select(Product).where(Product.sku == sku, Product.active == True)
                )
                product = result.scalar_one_or_none()
                
                PRODUCT_DATABASE_QUERIES.labels(query_type="select", status="success").inc()
                PRODUCT_OPERATIONS.labels(operation="get_by_sku", status="success").inc()
                
                return product
                
            except Exception as e:
                PRODUCT_DATABASE_QUERIES.labels(query_type="select", status="error").inc()
                PRODUCT_OPERATIONS.labels(operation="get_by_sku", status="error").inc()
                raise

    async def search_products(self, session: AsyncSession, query: str, skip: int = 0, limit: int = 50) -> List[Product]:
        """Search products by name or description."""
        with PRODUCT_OPERATION_DURATION.labels(operation="search").time():
            try:
                PRODUCT_DATABASE_QUERIES.labels(query_type="select", status="started").inc()
                PRODUCT_SEARCHES.labels(search_type="text").inc()
                
                result = await session.execute(
                    select(Product)
                    .where(
                        Product.active == True,
                        (Product.name.ilike(f"%{query}%") | Product.description.ilike(f"%{query}%"))
                    )
                    .offset(skip)
                    .limit(limit)
                    .order_by(Product.name)
                )
                products = result.scalars().all()
                
                PRODUCT_DATABASE_QUERIES.labels(query_type="select", status="success").inc()
                PRODUCT_OPERATIONS.labels(operation="search", status="success").inc()
                
                return list(products)
                
            except Exception as e:
                PRODUCT_DATABASE_QUERIES.labels(query_type="select", status="error").inc()
                PRODUCT_OPERATIONS.labels(operation="search", status="error").inc()
                raise

    async def create_product(self, session: AsyncSession, product_data: Dict[str, Any]) -> Product:
        """Create a new product."""
        with PRODUCT_OPERATION_DURATION.labels(operation="create").time():
            try:
                PRODUCT_DATABASE_QUERIES.labels(query_type="insert", status="started").inc()
                
                # Create new product instance
                product = Product(
                    name=product_data["name"],
                    description=product_data.get("description"),
                    price=product_data["price"],
                    category=product_data["category"],
                    sku=product_data["sku"],
                    active=product_data.get("active", True)
                )
                
                session.add(product)
                await session.commit()
                await session.refresh(product)
                
                PRODUCT_DATABASE_QUERIES.labels(query_type="insert", status="success").inc()
                PRODUCT_OPERATIONS.labels(operation="create", status="success").inc()
                
                # Update active products count
                await self._update_active_products_count(session)
                
                return product
                
            except IntegrityError as e:
                await session.rollback()
                PRODUCT_DATABASE_QUERIES.labels(query_type="insert", status="error").inc()
                PRODUCT_OPERATIONS.labels(operation="create", status="duplicate_sku").inc()
                raise ValueError(f"Product with SKU {product_data['sku']} already exists")
            except Exception as e:
                await session.rollback()
                PRODUCT_DATABASE_QUERIES.labels(query_type="insert", status="error").inc()
                PRODUCT_OPERATIONS.labels(operation="create", status="error").inc()
                raise

    async def update_product(self, session: AsyncSession, product_id: int, product_data: Dict[str, Any]) -> Optional[Product]:
        """Update an existing product."""
        with PRODUCT_OPERATION_DURATION.labels(operation="update").time():
            try:
                # First get the product
                product = await self.get_product_by_id(session, product_id)
                if not product:
                    PRODUCT_OPERATIONS.labels(operation="update", status="not_found").inc()
                    return None
                
                PRODUCT_DATABASE_QUERIES.labels(query_type="update", status="started").inc()
                
                # Update fields if provided
                if "name" in product_data and product_data["name"]:
                    product.name = product_data["name"]
                if "description" in product_data:
                    product.description = product_data["description"]
                if "price" in product_data and product_data["price"] is not None:
                    product.price = product_data["price"]
                if "category" in product_data and product_data["category"]:
                    product.category = product_data["category"]
                if "sku" in product_data and product_data["sku"]:
                    product.sku = product_data["sku"]
                if "active" in product_data:
                    product.active = product_data["active"]
                
                product.updated_at = datetime.utcnow()
                
                await session.commit()
                await session.refresh(product)
                
                PRODUCT_DATABASE_QUERIES.labels(query_type="update", status="success").inc()
                PRODUCT_OPERATIONS.labels(operation="update", status="success").inc()
                
                return product
                
            except IntegrityError as e:
                await session.rollback()
                PRODUCT_DATABASE_QUERIES.labels(query_type="update", status="error").inc()
                PRODUCT_OPERATIONS.labels(operation="update", status="duplicate_sku").inc()
                raise ValueError(f"SKU {product_data.get('sku')} is already taken")
            except Exception as e:
                await session.rollback()
                PRODUCT_DATABASE_QUERIES.labels(query_type="update", status="error").inc()
                PRODUCT_OPERATIONS.labels(operation="update", status="error").inc()
                raise

    async def delete_product(self, session: AsyncSession, product_id: int) -> bool:
        """Soft delete a product (mark as inactive)."""
        with PRODUCT_OPERATION_DURATION.labels(operation="delete").time():
            try:
                # Get the product first
                product = await self.get_product_by_id(session, product_id)
                if not product:
                    PRODUCT_OPERATIONS.labels(operation="delete", status="not_found").inc()
                    return False
                
                PRODUCT_DATABASE_QUERIES.labels(query_type="update", status="started").inc()
                
                # Soft delete by marking as inactive
                product.active = False
                product.updated_at = datetime.utcnow()
                
                await session.commit()
                
                PRODUCT_DATABASE_QUERIES.labels(query_type="update", status="success").inc()
                PRODUCT_OPERATIONS.labels(operation="delete", status="success").inc()
                
                # Update active products count
                await self._update_active_products_count(session)
                
                return True
                
            except Exception as e:
                await session.rollback()
                PRODUCT_DATABASE_QUERIES.labels(query_type="update", status="error").inc()
                PRODUCT_OPERATIONS.labels(operation="delete", status="error").inc()
                raise

    async def get_categories(self, session: AsyncSession) -> List[str]:
        """Get all unique product categories."""
        with PRODUCT_OPERATION_DURATION.labels(operation="get_categories").time():
            try:
                PRODUCT_DATABASE_QUERIES.labels(query_type="select", status="started").inc()
                
                result = await session.execute(
                    select(Product.category)
                    .where(Product.active == True)
                    .distinct()
                    .order_by(Product.category)
                )
                categories = result.scalars().all()
                
                PRODUCT_DATABASE_QUERIES.labels(query_type="select", status="success").inc()
                PRODUCT_OPERATIONS.labels(operation="get_categories", status="success").inc()
                
                return list(categories)
                
            except Exception as e:
                PRODUCT_DATABASE_QUERIES.labels(query_type="select", status="error").inc()
                PRODUCT_OPERATIONS.labels(operation="get_categories", status="error").inc()
                raise

    async def get_product_count(self, session: AsyncSession) -> int:
        """Get total count of active products."""
        with PRODUCT_OPERATION_DURATION.labels(operation="count").time():
            try:
                PRODUCT_DATABASE_QUERIES.labels(query_type="count", status="started").inc()
                
                result = await session.execute(
                    select(Product.id).where(Product.active == True)
                )
                count = len(result.scalars().all())
                
                PRODUCT_DATABASE_QUERIES.labels(query_type="count", status="success").inc()
                PRODUCT_OPERATIONS.labels(operation="count", status="success").inc()
                
                return count
                
            except Exception as e:
                PRODUCT_DATABASE_QUERIES.labels(query_type="count", status="error").inc()
                PRODUCT_OPERATIONS.labels(operation="count", status="error").inc()
                raise

    async def _update_active_products_count(self, session: AsyncSession) -> None:
        """Update the active products gauge metric."""
        try:
            count = await self.get_product_count(session)
            ACTIVE_PRODUCTS.set(count)
        except Exception:
            # Don't fail the main operation if metrics update fails
            pass

# Global service instance
product_service = ProductService()