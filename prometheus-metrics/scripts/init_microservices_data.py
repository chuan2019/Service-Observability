#!/usr/bin/env python3
"""
Sample data initialization for microservices via HTTP API.
Creates sample users, products, and inventory via the API Gateway.
"""

import asyncio
import aiohttp
import random
from typing import List, Dict, Any


class MicroservicesDataInitializer:
    """Initialize sample data for microservices via HTTP API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.created_users = []
        self.created_products = []

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def create_sample_users(self) -> List[Dict[str, Any]]:
        """Create sample users via API."""
        print("Creating sample users...")
        
        sample_users = [
            {
                "name": "John Doe",
                "email": "john.doe@example.com",
                "address": "123 Main St, Anytown, USA 12345",
                "phone": "+1-555-0101"
            },
            {
                "name": "Jane Smith",
                "email": "jane.smith@example.com",
                "address": "456 Oak Ave, Springfield, USA 67890",
                "phone": "+1-555-0102"
            },
            {
                "name": "Bob Johnson",
                "email": "bob.johnson@example.com",
                "address": "789 Pine Rd, Riverside, USA 11111",
                "phone": "+1-555-0103"
            },
            {
                "name": "Alice Brown",
                "email": "alice.brown@example.com",
                "address": "321 Elm St, Westside, USA 22222",
                "phone": "+1-555-0104"
            },
            {
                "name": "Charlie Wilson",
                "email": "charlie.wilson@example.com",
                "address": "654 Cedar Blvd, Northtown, USA 33333",
                "phone": "+1-555-0105"
            }
        ]

        created_users = []
        for user_data in sample_users:
            try:
                async with self.session.post(
                    f"{self.base_url}/api/users",
                    json=user_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        user = await response.json()
                        created_users.append(user)
                        print(f"Created user: {user['name']} (ID: {user['id']})")
                    else:
                        error_text = await response.text()
                        print(f"Failed to create user {user_data['name']}: {error_text}")
            except Exception as e:
                print(f"Error creating user {user_data['name']}: {e}")

        self.created_users = created_users
        print(f"Created {len(created_users)} users")
        return created_users

    async def create_sample_products(self) -> List[Dict[str, Any]]:
        """Create sample products via API."""
        print("Creating sample products...")
        
        sample_products = [
            {
                "name": "Laptop Pro 15",
                "description": "High-performance laptop with 15-inch display",
                "price": 1299.99,
                "category": "Electronics",
                "sku": "LAP-PRO-15"
            },
            {
                "name": "Wireless Mouse",
                "description": "Ergonomic wireless mouse with precision tracking",
                "price": 29.99,
                "category": "Electronics",
                "sku": "MSE-WL-001"
            },
            {
                "name": "Mechanical Keyboard",
                "description": "RGB mechanical keyboard with blue switches",
                "price": 149.99,
                "category": "Electronics",
                "sku": "KBD-MCH-RGB"
            },
            {
                "name": "4K Monitor",
                "description": "27-inch 4K UHD monitor with HDR support",
                "price": 399.99,
                "category": "Electronics",
                "sku": "MON-4K-27"
            },
            {
                "name": "USB-C Hub",
                "description": "Multi-port USB-C hub with HDMI and ethernet",
                "price": 79.99,
                "category": "Electronics",
                "sku": "HUB-USBC-MP"
            },
            {
                "name": "Desk Chair",
                "description": "Ergonomic office chair with lumbar support",
                "price": 299.99,
                "category": "Furniture",
                "sku": "CHR-ERG-001"
            },
            {
                "name": "Standing Desk",
                "description": "Height-adjustable standing desk",
                "price": 599.99,
                "category": "Furniture",
                "sku": "DSK-STD-ADJ"
            },
            {
                "name": "Desk Lamp",
                "description": "LED desk lamp with adjustable brightness",
                "price": 49.99,
                "category": "Furniture",
                "sku": "LMP-LED-DSK"
            },
            {
                "name": "Coffee Mug",
                "description": "Insulated coffee mug with lid",
                "price": 19.99,
                "category": "Kitchen",
                "sku": "MUG-INS-001"
            },
            {
                "name": "Water Bottle",
                "description": "Stainless steel water bottle 32oz",
                "price": 24.99,
                "category": "Kitchen",
                "sku": "BTL-SS-32OZ"
            }
        ]

        created_products = []
        for product_data in sample_products:
            try:
                async with self.session.post(
                    f"{self.base_url}/api/products",
                    json=product_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        product = await response.json()
                        created_products.append(product)
                        print(f"Created product: {product['name']} (ID: {product['id']})")
                    else:
                        error_text = await response.text()
                        print(f"Failed to create product {product_data['name']}: {error_text}")
            except Exception as e:
                print(f"Error creating product {product_data['name']}: {e}")

        self.created_products = created_products
        print(f"Created {len(created_products)} products")
        return created_products

    async def create_sample_inventory(self) -> None:
        """Create sample inventory for products via API."""
        if not self.created_products:
            print("No products available for inventory creation")
            return

        print("Creating sample inventory...")
        
        for product in self.created_products:
            # Random stock quantities
            available_quantity = random.randint(10, 100)
            reorder_level = random.randint(5, 15)
            
            inventory_data = {
                "product_id": product["id"],
                "available_quantity": available_quantity,
                "reorder_level": reorder_level
            }
            
            try:
                async with self.session.post(
                    f"{self.base_url}/api/inventory",
                    json=inventory_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        inventory = await response.json()
                        print(f"Created inventory for {product['name']}: {available_quantity} units")
                    else:
                        error_text = await response.text()
                        print(f"Failed to create inventory for {product['name']}: {error_text}")
            except Exception as e:
                print(f"Error creating inventory for {product['name']}: {e}")

    async def check_services_health(self) -> bool:
        """Check if all required services are healthy."""
        print("Checking services health...")
        
        try:
            async with self.session.get(f"{self.base_url}/health/services") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"API Gateway: {health_data.get('gateway', 'unknown')}")
                    
                    services = health_data.get('services', {})
                    all_healthy = True
                    
                    for service_name, service_health in services.items():
                        status = service_health.get('status', 'unknown')
                        print(f"{service_name}: {status}")
                        if status != 'healthy':
                            all_healthy = False
                    
                    return all_healthy
                else:
                    print(f"Health check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"Error checking services health: {e}")
            return False

    async def initialize_all_data(self) -> None:
        """Initialize all sample data."""
        print("Starting sample data initialization...")
        print("=" * 50)
        
        # Check services health first
        if not await self.check_services_health():
            print("Some services are not healthy. Please ensure all services are running.")
            return
        
        print()
        
        # Create sample data
        await self.create_sample_users()
        print()
        
        await self.create_sample_products()
        print()
        
        await self.create_sample_inventory()
        print()
        
        print("=" * 50)
        print("Sample data initialization completed!")
        print(f"Created {len(self.created_users)} users")
        print(f"Created {len(self.created_products)} products")
        print("Inventory created for all products")
        print()
        print("You can now test the microservices with sample data!")


async def main():
    """Main function to initialize sample data."""
    async with MicroservicesDataInitializer() as initializer:
        await initializer.initialize_all_data()


if __name__ == "__main__":
    asyncio.run(main())