#!/usr/bin/env python3
"""
Traffic generation script for FastAPI Prometheus metrics demonstration.
Generates realistic traffic patterns to showcase metrics collection.
"""

import asyncio
import aiohttp
import random
import json
import time
from typing import List, Dict, Any
from datetime import datetime


class TrafficGenerator:
    """Generate realistic traffic for the FastAPI application."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.created_users = []
        self.created_orders = []
        self.created_payments = []

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def make_request(
        self, 
        method: str, 
        endpoint: str, 
        json_data: Dict[str, Any] = None,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make an HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(
                method, 
                url, 
                json=json_data,
                params=params
            ) as response:
                if response.content_type == 'application/json':
                    return {
                        "status": response.status,
                        "data": await response.json(),
                        "success": response.status < 400
                    }
                else:
                    return {
                        "status": response.status,
                        "data": await response.text(),
                        "success": response.status < 400
                    }
        except Exception as e:
            print(f"Error making {method} request to {url}: {e}")
            return {
                "status": 0,
                "data": {"error": str(e)},
                "success": False
            }

    # Add all the new traffic generation methods here...
    async def generate_mixed_traffic(self, duration_minutes: int = 10):
        """Generate mixed traffic for specified duration with realistic patterns."""
        end_time = time.time() + (duration_minutes * 60)
        request_count = 0
        
        print(f"Starting realistic traffic generation for {duration_minutes} minutes...")
        
        while time.time() < end_time:
            # Define realistic traffic distribution
            traffic_types = [
                (self.generate_basic_traffic, 0.4),      # 40% basic traffic
                (self.generate_user_traffic, 0.25),      # 25% user operations  
                (self.generate_order_traffic, 0.25),     # 25% order operations
                (self.generate_payment_traffic, 0.1),    # 10% payment operations
            ]
            
            # Select traffic type based on distribution
            rand = random.random()
            cumulative = 0
            
            for traffic_func, weight in traffic_types:
                cumulative += weight
                if rand <= cumulative:
                    await traffic_func()
                    break
            
            request_count += 1
            
            # Print progress every 25 requests
            if request_count % 25 == 0:
                remaining_time = max(0, end_time - time.time())
                print(f"Progress: {request_count} requests, {remaining_time/60:.1f} min remaining")
            
            # Realistic delay between requests (0.5 to 5 seconds)
            await asyncio.sleep(random.uniform(0.5, 5.0))
        
        print(f"Traffic generation completed! Total requests: {request_count}")

    async def generate_basic_traffic(self):
        """Generate basic endpoint traffic."""
        endpoints = [
            ("GET", "/"),
            ("GET", "/health"),
            ("GET", "/metrics"),
        ]
        
        method, endpoint = random.choice(endpoints)
        result = await self.make_request(method, endpoint)
        if result["success"]:
            print(f"SUCCESS: {method} {endpoint}")

    async def generate_user_traffic(self):
        """Generate user-related traffic."""
        operations = [
            ("GET", "/api/v1/users"),
            ("GET", f"/api/v1/users/{random.randint(1, 5)}"),
            ("POST", "/api/v1/users", {
                "name": f"User {random.randint(1000, 9999)}",
                "email": f"user{random.randint(1000, 9999)}@example.com"
            })
        ]
        
        method, endpoint, *data = random.choice(operations)
        json_data = data[0] if data else None
        result = await self.make_request(method, endpoint, json_data)
        if result["success"]:
            print(f"SUCCESS: User operation: {method} {endpoint}")

    async def generate_order_traffic(self):
        """Generate order-related traffic."""
        operations = [
            ("GET", "/api/v1/orders"),
            ("GET", f"/api/v1/orders/{random.randint(101, 105)}"),
            ("POST", "/api/v1/orders", {
                "user_id": random.randint(1, 3),
                "amount": round(random.uniform(20, 200), 2),
                "items": [f"item_{i}" for i in range(1, random.randint(2, 5))],
                "type": random.choice(["standard", "express"])
            })
        ]
        
        method, endpoint, *data = random.choice(operations)
        json_data = data[0] if data else None
        result = await self.make_request(method, endpoint, json_data)
        if result["success"]:
            print(f"SUCCESS: Order operation: {method} {endpoint}")

    async def generate_payment_traffic(self):
        """Generate payment-related traffic."""
        operations = [
            ("POST", "/api/v1/payments", {
                "order_id": random.choice([101, 102]),
                "amount": round(random.uniform(20, 200), 2),
                "method": random.choice(["credit_card", "paypal"])
            }),
            ("GET", f"/api/v1/payments/{random.randint(1001, 1005)}"),
        ]
        
        method, endpoint, *data = random.choice(operations)
        json_data = data[0] if data else None
        result = await self.make_request(method, endpoint, json_data)
        if result["success"]:
            print(f"SUCCESS: Payment operation: {method} {endpoint}")


async def main():
    """Main function to run traffic generation."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="FastAPI Prometheus Metrics Traffic Generator")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the FastAPI application")
    parser.add_argument("--duration", type=int, default=5, help="Duration in minutes to generate traffic")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("FastAPI Prometheus Metrics Traffic Generator")
    print("=" * 60)
    print(f"Target URL: {args.url}")
    print(f"⏱️  Duration: {args.duration} minutes")
    print("=" * 60)
    
    async with TrafficGenerator(args.url) as generator:
        # Test connection first
        result = await generator.make_request("GET", "/health")
        if not result["success"]:
            print(f"ERROR: Cannot connect to {args.url}. Please ensure the FastAPI application is running.")
            return
        
        print(f"Successfully connected to {args.url}")
        await generator.generate_mixed_traffic(args.duration)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTraffic generation stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        import sys
        sys.exit(1)