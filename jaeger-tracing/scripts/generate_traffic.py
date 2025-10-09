#!/usr/bin/env python3
"""Traffic generation script for FastAPI Jaeger tracing demo."""

import asyncio
import random
import time
from typing import List, Dict, Any
import httpx
import argparse
import json
from datetime import datetime


class TrafficGenerator:
    """Generate realistic traffic for the FastAPI demo application."""
    
    def __init__(self, base_url: str = "http://localhost:8000", concurrent_requests: int = 5):
        self.base_url = base_url.rstrip('/')
        self.concurrent_requests = concurrent_requests
        self.session_timeout = httpx.Timeout(30.0)
        
    async def generate_user_activity(self, client: httpx.AsyncClient, duration: int = 60) -> None:
        """Generate realistic user activity patterns."""
        print(f"Starting user activity generation for {duration} seconds...")
        
        start_time = time.time()
        request_count = 0
        
        while time.time() - start_time < duration:
            try:
                # Choose a random activity pattern
                activity = random.choices(
                    ["browse", "create_user", "full_flow", "error_scenario"],
                    weights=[40, 20, 30, 10],
                    k=1
                )[0]
                
                if activity == "browse":
                    await self._browse_pattern(client)
                elif activity == "create_user":
                    await self._create_user_pattern(client)
                elif activity == "full_flow":
                    await self._full_flow_pattern(client)
                elif activity == "error_scenario":
                    await self._error_scenario_pattern(client)
                
                request_count += 1
                
                # Random delay between activities
                await asyncio.sleep(random.uniform(0.5, 3.0))
                
            except Exception as e:
                print(f"Error in activity generation: {e}")
                await asyncio.sleep(1.0)
        
        print(f"Completed user activity generation. Total patterns executed: {request_count}")
    
    async def _browse_pattern(self, client: httpx.AsyncClient) -> None:
        """Simulate browsing behavior."""
        # Health check
        await client.get(f"{self.base_url}/health")
        
        # Browse users
        user_id = random.randint(1, 3)
        await client.get(f"{self.base_url}/users/{user_id}")
        
        # Maybe check an order
        if random.random() > 0.5:
            order_id = random.randint(101, 102)
            try:
                await client.get(f"{self.base_url}/orders/{order_id}")
            except httpx.HTTPStatusError:
                pass  # Order might not exist, that's ok
    
    async def _create_user_pattern(self, client: httpx.AsyncClient) -> None:
        """Simulate user creation."""
        user_data = {
            "name": f"User {random.randint(1000, 9999)}",
            "email": f"user{random.randint(1000, 9999)}@example.com"
        }
        
        try:
            response = await client.post(f"{self.base_url}/users", json=user_data)
            if response.status_code == 200:
                user = response.json()
                print(f"Created user: {user['name']} (ID: {user['id']})")
        except httpx.HTTPStatusError as e:
            print(f"Failed to create user: {e}")
    
    async def _full_flow_pattern(self, client: httpx.AsyncClient) -> None:
        """Simulate full e-commerce flow."""
        user_id = random.randint(1, 3)
        
        try:
            # Get user
            await client.get(f"{self.base_url}/users/{user_id}")
            
            # Create order
            order_data = {
                "user_id": user_id,
                "amount": round(random.uniform(10.0, 200.0), 2),
                "items": [f"item_{i}" for i in range(random.randint(1, 5))]
            }
            
            order_response = await client.post(f"{self.base_url}/orders", json=order_data)
            if order_response.status_code == 200:
                order = order_response.json()
                
                # Process payment
                payment_data = {
                    "order_id": order["id"],
                    "amount": order["amount"],
                    "method": random.choice(["credit_card", "debit_card", "paypal"])
                }
                
                payment_response = await client.post(f"{self.base_url}/payments", json=payment_data)
                if payment_response.status_code == 200:
                    payment = payment_response.json()
                    print(f"Completed full flow: User {user_id} -> Order {order['id']} -> Payment {payment['id']}")
                
        except httpx.HTTPStatusError as e:
            print(f"Full flow failed: {e}")
    
    async def _error_scenario_pattern(self, client: httpx.AsyncClient) -> None:
        """Simulate error scenarios for testing."""
        scenarios = [
            ("invalid_user", lambda: client.get(f"{self.base_url}/users/999")),
            ("invalid_order", lambda: client.get(f"{self.base_url}/orders/999")),
            ("invalid_order_data", lambda: client.post(f"{self.base_url}/orders", json={"invalid": "data"})),
            ("invalid_payment_data", lambda: client.post(f"{self.base_url}/payments", json={"invalid": "data"})),
        ]
        
        scenario_name, scenario_func = random.choice(scenarios)
        
        try:
            await scenario_func()
        except httpx.HTTPStatusError:
            print(f"Generated expected error scenario: {scenario_name}")
        except Exception as e:
            print(f"Unexpected error in scenario {scenario_name}: {e}")
    
    async def demo_full_flow(self, client: httpx.AsyncClient) -> None:
        """Demonstrate the full flow endpoint for tracing."""
        user_id = random.randint(1, 3)
        
        try:
            response = await client.get(f"{self.base_url}/demo/full-flow/{user_id}")
            if response.status_code == 200:
                result = response.json()
                print(f"Demo full flow completed for user {user_id}")
                print(f"   Order ID: {result['order']['id']}, Payment Status: {result['payment']['status']}")
            else:
                print(f"Demo full flow failed with status: {response.status_code}")
        except Exception as e:
            print(f"Demo full flow error: {e}")
    
    async def stress_test(self, client: httpx.AsyncClient, requests_per_second: int = 10, duration: int = 30) -> None:
        """Generate stress test traffic."""
        print(f"Starting stress test: {requests_per_second} RPS for {duration} seconds...")
        
        request_interval = 1.0 / requests_per_second
        start_time = time.time()
        request_count = 0
        success_count = 0
        error_count = 0
        
        while time.time() - start_time < duration:
            try:
                # Create multiple concurrent requests
                tasks = []
                for _ in range(min(requests_per_second, self.concurrent_requests)):
                    endpoint = random.choice([
                        "/health",
                        "/users/1",
                        "/users/2", 
                        "/orders/101",
                        f"/demo/full-flow/{random.randint(1, 3)}"
                    ])
                    tasks.append(client.get(f"{self.base_url}{endpoint}"))
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                for response in responses:
                    request_count += 1
                    if isinstance(response, Exception):
                        error_count += 1
                    else:
                        success_count += 1
                
                await asyncio.sleep(request_interval)
                
            except Exception as e:
                print(f"Stress test error: {e}")
                error_count += 1
        
        print(f"Stress test completed:")
        print(f"   Total requests: {request_count}")
        print(f"   Successful: {success_count}")
        print(f"   Errors: {error_count}")
        print(f"   Success rate: {success_count/request_count*100:.1f}%")


async def main():
    parser = argparse.ArgumentParser(description="FastAPI Jaeger Tracing Traffic Generator")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the FastAPI application")
    parser.add_argument("--mode", choices=["activity", "demo", "stress"], default="activity", 
                       help="Traffic generation mode")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds")
    parser.add_argument("--concurrent", type=int, default=5, help="Number of concurrent requests")
    parser.add_argument("--rps", type=int, default=10, help="Requests per second (stress mode only)")
    
    args = parser.parse_args()
    
    generator = TrafficGenerator(args.url, args.concurrent)
    
    print(f"FastAPI Jaeger Tracing Traffic Generator")
    print(f"   URL: {args.url}")
    print(f"   Mode: {args.mode}")
    print(f"   Duration: {args.duration}s")
    print(f"   Concurrent requests: {args.concurrent}")
    print()
    
    async with httpx.AsyncClient(timeout=generator.session_timeout) as client:
        # Test connection
        try:
            response = await client.get(f"{args.url}/health")
            print(f"Connected to FastAPI application (Status: {response.status_code})")
        except Exception as e:
            print(f"Failed to connect to {args.url}: {e}")
            return
        
        # Generate traffic based on mode
        if args.mode == "activity":
            await generator.generate_user_activity(client, args.duration)
        elif args.mode == "demo":
            print("Running demo flow scenarios...")
            for i in range(5):
                await generator.demo_full_flow(client)
                await asyncio.sleep(2)
        elif args.mode == "stress":
            await generator.stress_test(client, args.rps, args.duration)
    
    print(f"\nTraffic generation completed!")
    print(f"   Check Jaeger UI at: http://localhost:16686")
    print(f"   Look for traces from service: fastapi-jaeger-demo")


if __name__ == "__main__":
    asyncio.run(main())