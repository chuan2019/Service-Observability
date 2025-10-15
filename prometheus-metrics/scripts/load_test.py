#!/usr/bin/env python3
"""Load testing script for the e-commerce microservices API."""

import asyncio
import aiohttp
import argparse
import random
import time
from typing import Dict

# API endpoints
BASE_URL = "http://localhost:8000"
ENDPOINTS = {
    "users": "/api/users",
    "products": "/api/products",
    "inventory": "/api/inventory",
    "orders": "/api/orders",
    "payments": "/api/payments",
    "notifications": "/api/notifications",
    "health": "/health",
    "services_health": "/health/services",
    "metrics": "/metrics"
}

# Sample data for testing
SAMPLE_USERS = [
    "john.doe@example.com",
    "jane.smith@example.com", 
    "bob.johnson@example.com",
    "alice.brown@example.com",
    "charlie.wilson@example.com"
]

SAMPLE_PRODUCTS = [
    "WBH-001", "SFW-002", "OCT-003", "SSW-004", "PCM-005",
    "YMP-006", "WPC-007", "RSU-008", "KKS-009", "PBS-010"
]

SAMPLE_USER_IDS = [1, 2, 3, 4, 5]
SAMPLE_PRODUCT_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
SAMPLE_ORDER_IDS = [1, 2, 3, 4, 5]
SAMPLE_PAYMENT_IDS = [1, 2, 3, 4, 5]

class LoadTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = None
        self.stats = {
            "requests": 0,
            "successes": 0,
            "errors": 0,
            "avg_response_time": 0
        }
        self.response_times = []

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def make_request(self, method: str, url: str, **kwargs) -> Dict:
        """Make HTTP request and track stats."""
        start_time = time.time()
        
        try:
            self.stats["requests"] += 1
            
            async with self.session.request(method, url, **kwargs) as response:
                response_time = time.time() - start_time
                self.response_times.append(response_time)
                
                if response.status < 400:
                    self.stats["successes"] += 1
                else:
                    self.stats["errors"] += 1
                
                return {
                    "status": response.status,
                    "response_time": response_time,
                    "url": url
                }
                
        except Exception as e:
            response_time = time.time() - start_time
            self.response_times.append(response_time)
            self.stats["errors"] += 1
            
            return {
                "status": 0,
                "response_time": response_time,
                "url": url,
                "error": str(e)
            }

    async def test_health_check(self) -> Dict:
        """Test health check endpoint."""
        url = f"{self.base_url}{ENDPOINTS['health']}"
        return await self.make_request("GET", url)

    async def test_services_health(self) -> Dict:
        """Test all services health check endpoint."""
        url = f"{self.base_url}{ENDPOINTS['services_health']}"
        return await self.make_request("GET", url)

    async def test_users_list(self) -> Dict:
        """Test users list endpoint."""
        url = f"{self.base_url}{ENDPOINTS['users']}"
        return await self.make_request("GET", url)

    async def test_user_get(self) -> Dict:
        """Test get single user endpoint."""
        user_id = random.choice(SAMPLE_USER_IDS)
        url = f"{self.base_url}{ENDPOINTS['users']}/{user_id}"
        return await self.make_request("GET", url)

    async def test_products_list(self) -> Dict:
        """Test products list endpoint."""
        url = f"{self.base_url}{ENDPOINTS['products']}"
        return await self.make_request("GET", url)

    async def test_product_get(self) -> Dict:
        """Test get single product endpoint."""
        product_id = random.choice(SAMPLE_PRODUCT_IDS)
        url = f"{self.base_url}{ENDPOINTS['products']}/{product_id}"
        return await self.make_request("GET", url)

    async def test_inventory_list(self) -> Dict:
        """Test inventory list endpoint."""
        url = f"{self.base_url}{ENDPOINTS['inventory']}"
        return await self.make_request("GET", url)

    async def test_inventory_get(self) -> Dict:
        """Test get inventory for specific product."""
        product_id = random.choice(SAMPLE_PRODUCT_IDS)
        url = f"{self.base_url}{ENDPOINTS['inventory']}/{product_id}"
        return await self.make_request("GET", url)

    async def test_orders_list(self) -> Dict:
        """Test orders list endpoint."""
        url = f"{self.base_url}{ENDPOINTS['orders']}"
        return await self.make_request("GET", url)

    async def test_order_get(self) -> Dict:
        """Test get single order endpoint."""
        order_id = random.choice(SAMPLE_ORDER_IDS)
        url = f"{self.base_url}{ENDPOINTS['orders']}/{order_id}"
        return await self.make_request("GET", url)

    async def test_orders_by_user(self) -> Dict:
        """Test get orders by user endpoint."""
        user_id = random.choice(SAMPLE_USER_IDS)
        url = f"{self.base_url}{ENDPOINTS['orders']}/user/{user_id}"
        return await self.make_request("GET", url)

    async def test_payments_list(self) -> Dict:
        """Test payments list endpoint."""
        url = f"{self.base_url}{ENDPOINTS['payments']}"
        return await self.make_request("GET", url)

    async def test_payment_get(self) -> Dict:
        """Test get single payment endpoint."""
        payment_id = random.choice(SAMPLE_PAYMENT_IDS)
        url = f"{self.base_url}{ENDPOINTS['payments']}/{payment_id}"
        return await self.make_request("GET", url)

    async def test_notifications_list(self) -> Dict:
        """Test notifications list endpoint."""
        url = f"{self.base_url}{ENDPOINTS['notifications']}"
        return await self.make_request("GET", url)

    async def test_notification_get(self) -> Dict:
        """Test get single notification endpoint."""
        notification_id = random.randint(1, 10)
        url = f"{self.base_url}{ENDPOINTS['notifications']}/{notification_id}"
        return await self.make_request("GET", url)

    async def test_notifications_by_user(self) -> Dict:
        """Test get notifications by user endpoint."""
        user_id = random.choice(SAMPLE_USER_IDS)
        url = f"{self.base_url}{ENDPOINTS['notifications']}/user/{user_id}"
        return await self.make_request("GET", url)

    async def run_mixed_load(self, duration: int = 60, concurrent_requests: int = 5):
        """Run mixed load test for specified duration."""
        print(f"Starting load test for {duration} seconds with {concurrent_requests} concurrent requests")
        print(f"Targeting: {self.base_url}")
        print("-" * 60)
        
        start_time = time.time()
        tasks = []
        
        async def worker():
            while time.time() - start_time < duration:
                # Weighted random selection of test types for all services
                test_weights = [
                    (self.test_health_check, 5),           # 5% health checks
                    (self.test_services_health, 5),        # 5% services health
                    (self.test_users_list, 10),            # 10% user list
                    (self.test_user_get, 10),              # 10% user get
                    (self.test_products_list, 10),         # 10% product list
                    (self.test_product_get, 10),           # 10% product get
                    (self.test_inventory_list, 8),         # 8% inventory list
                    (self.test_inventory_get, 8),          # 8% inventory get
                    (self.test_orders_list, 8),            # 8% orders list
                    (self.test_order_get, 6),              # 6% order get
                    (self.test_orders_by_user, 5),         # 5% orders by user
                    (self.test_payments_list, 5),          # 5% payments list
                    (self.test_payment_get, 5),            # 5% payment get
                    (self.test_notifications_list, 3),     # 3% notifications list
                    (self.test_notification_get, 1),       # 1% notification get
                    (self.test_notifications_by_user, 1),  # 1% notifications by user
                ]
                
                # Weighted random selection
                weights = [w for _, w in test_weights]
                selected_test = random.choices(test_weights, weights=weights)[0][0]
                
                # Execute test
                result = await selected_test()
                
                # Print status for interesting results
                if result["status"] == 0 or result["status"] >= 400:
                    print(f"ERROR: {result['url']} - Status: {result['status']} - Time: {result['response_time']:.3f}s")
                elif result["response_time"] > 1.0:
                    print(f"WARNING: {result['url']} - Status: {result['status']} - Time: {result['response_time']:.3f}s (slow)")
                
                # Small delay between requests per worker
                await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Start concurrent workers
        for i in range(concurrent_requests):
            tasks.append(asyncio.create_task(worker()))
        
        # Wait for completion
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Calculate final stats
        if self.response_times:
            self.stats["avg_response_time"] = sum(self.response_times) / len(self.response_times)
            self.stats["min_response_time"] = min(self.response_times)
            self.stats["max_response_time"] = max(self.response_times)
            self.stats["p95_response_time"] = sorted(self.response_times)[int(len(self.response_times) * 0.95)]
        
        self.print_summary()

    def print_summary(self):
        """Print load test summary."""
        print("\n" + "=" * 60)
        print("LOAD TEST SUMMARY")
        print("=" * 60)
        print(f"Total Requests:     {self.stats['requests']}")
        print(f"Successful:         {self.stats['successes']} ({self.stats['successes']/self.stats['requests']*100:.1f}%)")
        print(f"Errors:             {self.stats['errors']} ({self.stats['errors']/self.stats['requests']*100:.1f}%)")
        print(f"Average Response:   {self.stats['avg_response_time']:.3f}s")
        
        if 'min_response_time' in self.stats:
            print(f"Min Response:       {self.stats['min_response_time']:.3f}s")
            print(f"Max Response:       {self.stats['max_response_time']:.3f}s")
            print(f"95th Percentile:    {self.stats['p95_response_time']:.3f}s")
        
        print(f"Requests/sec:       {self.stats['requests']/60:.2f}")
        print("=" * 60)
        print("Check metrics at: http://localhost:8000/metrics")
        print("View Grafana at:  http://localhost:3000")
        print("=" * 60)


async def main():
    """Main load testing function."""
    print("E-Commerce Microservices Load Tester")
    print("=" * 60)

    parser = argparse.ArgumentParser(
        description="Load testing script for e-commerce microservices API"
    )
    parser.add_argument(
        "--duration", type=int, default=60,
        help="Duration of the load test in seconds (default: 60)"
    )
    parser.add_argument(
        "--concurrent-requests", type=int, default=5,
        help="Number of concurrent requests to make (default: 5)"
    )

    args = parser.parse_args()
    duration = args.duration
    concurrent_requests = args.concurrent_requests
    
    try:
        async with LoadTester() as tester:
            # Quick connectivity test
            print("Testing connectivity...")
            health_result = await tester.test_health_check()
            
            if health_result["status"] != 200:
                print(f"ERROR: Health check failed: {health_result}")
                print("Please ensure the FastAPI server is running on http://localhost:8000")
                return
            
            print(f"Server is healthy (response time: {health_result['response_time']:.3f}s)")
            print()
            
            # Run main load test
            await tester.run_mixed_load(duration, concurrent_requests)
            
    except KeyboardInterrupt:
        print("\nLoad test interrupted by user")
    except Exception as e:
        print(f"Error during load test: {e}")


if __name__ == "__main__":
    print("Starting in 3 seconds... (Press Ctrl+C to cancel)")
    try:
        time.sleep(3)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCancelled by user")