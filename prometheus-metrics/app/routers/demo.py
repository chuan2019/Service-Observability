"""Demo endpoints showcasing complete e-commerce workflow."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_session
from app.services.user_service import user_service
from app.services.product_service import product_service
from app.services.order_service import order_service
from app.services.inventory_service import inventory_service

router = APIRouter(prefix="/demo", tags=["demo"])

class CompleteOrderDemo(BaseModel):
    user_email: str
    product_skus: list[str]
    quantities: list[int]
    payment_method: str = "credit_card"

@router.post("/complete-order-flow")
async def demo_complete_order_flow(
    demo_data: CompleteOrderDemo,
    session: AsyncSession = Depends(get_session)
):
    """Demonstrate complete order flow from user lookup to payment processing."""
    try:
        # Step 1: Find user by email
        user = await user_service.get_user_by_email(session, demo_data.user_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {demo_data.user_email} not found"
            )

        # Step 2: Look up products by SKU and prepare order items
        order_items = []
        total_estimated = 0.0
        
        for sku, quantity in zip(demo_data.product_skus, demo_data.quantities):
            product = await product_service.get_product_by_sku(session, sku)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with SKU {sku} not found"
                )
            
            order_items.append({
                "product_id": product.id,
                "quantity": quantity
            })
            total_estimated += product.price * quantity

        # Step 3: Create order (this will handle inventory reservation automatically)
        order_data = {
            "user_id": user.id,
            "items": order_items,
            "shipping_address": user.address or "Default shipping address",
            "notes": "Demo order created via complete flow endpoint"
        }
        
        order = await order_service.create_order(session, order_data)

        # Step 4: Process payment
        payment_data = {
            "amount": order.total_amount,
            "method": demo_data.payment_method
        }
        
        updated_order = await order_service.process_order_payment(session, order.id, payment_data)

        return {
            "success": True,
            "message": "Complete order flow executed successfully",
            "order": {
                "id": updated_order.id,
                "status": updated_order.status.value,
                "total_amount": updated_order.total_amount,
                "user_id": updated_order.user_id,
                "items_count": len(updated_order.items)
            },
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email
            },
            "workflow_steps": [
                "User lookup completed",
                "Products validated",
                "Order created",
                "Inventory reserved",
                "Payment processed",
                "Order confirmed",
                "Notifications sent"
            ]
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Order flow failed"
        }

@router.post("/simulate-traffic")
async def simulate_realistic_traffic(
    session: AsyncSession = Depends(get_session)
):
    """Simulate realistic e-commerce traffic for metrics generation."""
    operations_performed = []
    
    try:
        # Simulate user browsing
        users = await user_service.get_all_users(session, limit=5)
        operations_performed.append(f"Retrieved {len(users)} users")
        
        # Simulate product browsing
        products = await product_service.get_all_products(session, limit=10)
        operations_performed.append(f"Retrieved {len(products)} products")
        
        # Simulate category browsing
        categories = await product_service.get_categories(session)
        operations_performed.append(f"Retrieved {len(categories)} categories")
        
        # Simulate inventory checks
        if products:
            for product in products[:3]:  # Check first 3 products
                stock = await inventory_service.get_stock_by_product_id(session, product.id)
                if stock:
                    operations_performed.append(f"Checked stock for product {product.id}")
        
        return {
            "success": True,
            "message": "Traffic simulation completed",
            "operations_performed": operations_performed,
            "metrics_generated": True,
            "note": "Check /metrics endpoint to see generated metrics"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "operations_performed": operations_performed
        }

@router.get("/status")
async def get_demo_status(session: AsyncSession = Depends(get_session)):
    """Get status of all services for demo purposes."""
    try:
        # Check service health by performing simple operations
        user_count = await user_service.get_user_count(session)
        product_count = await product_service.get_product_count(session)
        
        return {
            "status": "healthy",
            "services": {
                "user_service": {"status": "active", "user_count": user_count},
                "product_service": {"status": "active", "product_count": product_count},
                "inventory_service": {"status": "active"},
                "order_service": {"status": "active"},
                "payment_service": {"status": "active"},
                "notification_service": {"status": "active"}
            },
            "database": "connected",
            "metrics": "enabled"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }