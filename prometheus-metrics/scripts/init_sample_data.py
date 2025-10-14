"""Sample data initialization for the e-commerce microservices."""

import asyncio
import sys
import os
from datetime import datetime

# Add the parent directory to Python path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session, init_db
from app.services.user_service import user_service
from app.services.product_service import product_service
from app.services.inventory_service import inventory_service


async def create_sample_users(session: AsyncSession):
    """Create sample users."""
    print("Creating sample users...")
    
    sample_users = [
        {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "address": "123 Main St, Anytown, USA 12345",
            "phone": "+1-555-0101",
            "active": True
        },
        {
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "address": "456 Oak Ave, Springfield, USA 67890",
            "phone": "+1-555-0102",
            "active": True
        },
        {
            "name": "Bob Johnson",
            "email": "bob.johnson@example.com",
            "address": "789 Pine Rd, Riverside, USA 11111",
            "phone": "+1-555-0103",
            "active": True
        },
        {
            "name": "Alice Brown",
            "email": "alice.brown@example.com",
            "address": "321 Elm St, Westside, USA 22222",
            "phone": "+1-555-0104",
            "active": True
        },
        {
            "name": "Charlie Wilson",
            "email": "charlie.wilson@example.com",
            "address": "654 Maple Dr, Easttown, USA 33333",
            "phone": "+1-555-0105",
            "active": True
        }
    ]
    
    created_users = []
    for user_data in sample_users:
        try:
            user = await user_service.create_user(session, user_data)
            created_users.append(user)
            print(f"Created user: {user.name} ({user.email})")
        except Exception as e:
            print(f"User {user_data['email']} already exists or error occurred: {e}")
    
    return created_users


async def create_sample_products(session: AsyncSession):
    """Create sample products."""
    print("Creating sample products...")
    
    sample_products = [
        {
            "name": "Wireless Bluetooth Headphones",
            "description": "High-quality wireless headphones with noise cancellation",
            "price": 99.99,
            "category": "Electronics",
            "sku": "WBH-001",
            "active": True
        },
        {
            "name": "Smart Fitness Watch",
            "description": "GPS-enabled fitness tracker with heart rate monitoring",
            "price": 249.99,
            "category": "Electronics",
            "sku": "SFW-002",
            "active": True
        },
        {
            "name": "Organic Cotton T-Shirt",
            "description": "Comfortable and sustainable organic cotton t-shirt",
            "price": 29.99,
            "category": "Clothing",
            "sku": "OCT-003",
            "active": True
        },
        {
            "name": "Stainless Steel Water Bottle",
            "description": "Insulated water bottle keeps drinks cold for 24 hours",
            "price": 34.99,
            "category": "Home & Garden",
            "sku": "SSW-004",
            "active": True
        },
        {
            "name": "Professional Coffee Maker",
            "description": "12-cup programmable coffee maker with thermal carafe",
            "price": 129.99,
            "category": "Home & Garden",
            "sku": "PCM-005",
            "active": True
        },
        {
            "name": "Yoga Mat Premium",
            "description": "Non-slip yoga mat made from eco-friendly materials",
            "price": 59.99,
            "category": "Sports",
            "sku": "YMP-006",
            "active": True
        },
        {
            "name": "Wireless Phone Charger",
            "description": "Fast wireless charging pad compatible with all Qi devices",
            "price": 39.99,
            "category": "Electronics",
            "sku": "WPC-007",
            "active": True
        },
        {
            "name": "Running Shoes Ultra",
            "description": "Lightweight running shoes with advanced cushioning technology",
            "price": 159.99,
            "category": "Sports",
            "sku": "RSU-008",
            "active": True
        },
        {
            "name": "Kitchen Knife Set",
            "description": "Professional 8-piece kitchen knife set with wooden block",
            "price": 89.99,
            "category": "Home & Garden",
            "sku": "KKS-009",
            "active": True
        },
        {
            "name": "Portable Bluetooth Speaker",
            "description": "Waterproof portable speaker with 20-hour battery life",
            "price": 79.99,
            "category": "Electronics",
            "sku": "PBS-010",
            "active": True
        }
    ]
    
    created_products = []
    for product_data in sample_products:
        try:
            product = await product_service.create_product(session, product_data)
            created_products.append(product)
            print(f"Created product: {product.name} (SKU: {product.sku})")
        except Exception as e:
            print(f"Product {product_data['sku']} already exists or error occurred: {e}")
    
    return created_products


async def create_sample_inventory(session: AsyncSession, products):
    """Create sample inventory for products."""
    print("Creating sample inventory...")
    
    import random
    
    for product in products:
        try:
            # Create varied stock levels
            if product.category == "Electronics":
                available_qty = random.randint(15, 50)
            elif product.category == "Clothing":
                available_qty = random.randint(25, 100)
            elif product.category == "Sports":
                available_qty = random.randint(10, 40)
            else:  # Home & Garden
                available_qty = random.randint(20, 60)
            
            reorder_level = max(5, available_qty // 4)  # Set reorder level to ~25% of stock
            
            # We'll use the inventory service's update_stock method
            stock = await inventory_service.update_stock(
                session, 
                product.id, 
                available_qty, 
                reorder_level
            )
            print(f"Created inventory for {product.name}: {available_qty} units (reorder at {reorder_level})")
            
        except Exception as e:
            print(f"Failed to create inventory for {product.name}: {e}")


async def initialize_sample_data():
    """Initialize all sample data."""
    print("Starting sample data initialization...")
    
    # Initialize database first
    await init_db()
    
    # Get database session
    async with AsyncSession() as session:
        from app.database import AsyncSessionLocal
        
    async_session = AsyncSessionLocal()
    async with async_session as session:
        try:
            # Create sample users
            users = await create_sample_users(session)
            
            # Create sample products
            products = await create_sample_products(session)
            
            # Create sample inventory
            if products:
                await create_sample_inventory(session, products)
            
            print("\n" + "="*50)
            print("Sample data initialization completed!")
            print(f"Created {len(users)} users")
            print(f"Created {len(products)} products")
            print("Created inventory for all products")
            print("="*50)
            
            print("\nYou can now:")
            print("1. Start the application: uvicorn app.main:app --reload")
            print("2. Check users: GET /api/v1/users")
            print("3. Check products: GET /api/v1/products")
            print("4. Check inventory: GET /api/v1/inventory/{product_id}")
            print("5. Try demo flow: POST /api/v1/demo/complete-order-flow")
            print("6. View metrics: GET /metrics")
            
        except Exception as e:
            print(f"Error during initialization: {e}")
            await session.rollback()
        finally:
            await session.close()


if __name__ == "__main__":
    print("E-Commerce Microservices Sample Data Initializer")
    print("=" * 50)
    asyncio.run(initialize_sample_data())