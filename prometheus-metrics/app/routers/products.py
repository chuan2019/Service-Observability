"""Product management API endpoints."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_session
from app.services.product_service import product_service
from app.models import Product

router = APIRouter(prefix="/products", tags=["Products"])

# Pydantic models for API
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    category: str
    sku: str
    active: bool = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    sku: Optional[str] = None
    active: Optional[bool] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    category: str
    sku: str
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProductsListResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    page: int
    size: int

@router.get("/", response_model=ProductsListResponse)
async def get_products(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    """Get all products with optional category filter and pagination."""
    products = await product_service.get_all_products(session, skip=skip, limit=limit, category=category)
    total = await product_service.get_product_count(session)
    
    return ProductsListResponse(
        products=[ProductResponse.model_validate(product) for product in products],
        total=total,
        page=skip // limit + 1,
        size=len(products)
    )

@router.get("/search", response_model=ProductsListResponse)
async def search_products(
    q: str = Query(..., description="Search query"),
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session)
):
    """Search products by name or description."""
    products = await product_service.search_products(session, q, skip=skip, limit=limit)
    
    return ProductsListResponse(
        products=[ProductResponse.model_validate(product) for product in products],
        total=len(products),  # Note: for search we don't calculate total separately
        page=skip // limit + 1,
        size=len(products)
    )

@router.get("/categories")
async def get_categories(session: AsyncSession = Depends(get_session)):
    """Get all product categories."""
    categories = await product_service.get_categories(session)
    return {"categories": categories}

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific product by ID."""
    product = await product_service.get_product_by_id(session, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )
    return ProductResponse.model_validate(product)

@router.get("/sku/{sku}", response_model=ProductResponse)
async def get_product_by_sku(
    sku: str,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific product by SKU."""
    product = await product_service.get_product_by_sku(session, sku)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with SKU {sku} not found"
        )
    return ProductResponse.model_validate(product)

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new product."""
    try:
        product = await product_service.create_product(session, product_data.model_dump())
        return ProductResponse.model_validate(product)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update an existing product."""
    try:
        product = await product_service.update_product(session, product_id, product_data.model_dump(exclude_unset=True))
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        return ProductResponse.model_validate(product)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Delete a product (soft delete)."""
    deleted = await product_service.delete_product(session, product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found"
        )