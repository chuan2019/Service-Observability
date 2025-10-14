#!/usr/bin/env python3
"""Load testing script for the e-commerce microservices API."""

import asyncio
import aiohttp
import json
import random
import time
from typing import List, Dict

# API endpoints
BASE_URL = "http://localhost:8000"
ENDPOINTS = {
    "users": "/api/v1/users/",
    "products": "/api/v1/products/",
    "products_search": "/api/v1/products/search",
    "health": "/health",
    "metrics": "/metrics",
    "complete_order": "/api/v1/demo/complete-order-flow"
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

SEARCH_TERMS = [
    "bluetooth", "headphones", "watch", "coffee", "yoga",
    "phone", "speaker", "bottle", "shoes", "knife"
]

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

    async def test_users_list(self) -> Dict:
        """Test users list endpoint."""
        url = f"{self.base_url}{ENDPOINTS['users']}"
        params = {
            "skip": random.randint(0, 2),
            "limit": random.randint(3, 10)
        }
        return await self.make_request("GET", url, params=params)

    async def test_products_list(self) -> Dict:
        """Test products list endpoint."""
        url = f"{self.base_url}{ENDPOINTS['products']}"
        params = {
            "skip": random.randint(0, 3),
            "size": random.randint(3, 8)
        }
        return await self.make_request("GET", url, params=params)

    async def test_product_search(self) -> Dict:
        """Test product search endpoint."""
        url = f"{self.base_url}{ENDPOINTS['products_search']}"
        params = {
            "q": random.choice(SEARCH_TERMS),
            "size": random.randint(3, 10)
        }
        return await self.make_request("GET", url, params=params)

    async def test_complete_order_flow(self) -> Dict:
        """Test complete order flow endpoint."""
        url = f"{self.base_url}{ENDPOINTS['complete_order']}"
        
        # Random order data
        num_items = random.randint(1, 3)
        selected_skus = random.sample(SAMPLE_PRODUCTS, num_items)
        quantities = [random.randint(1, 3) for _ in range(num_items)]
        
        order_data = {
            "user_email": random.choice(SAMPLE_USERS),
            "product_skus": selected_skus,
            "quantities": quantities,
            "payment_method": random.choice(["credit_card", "debit_card", "paypal"])
        }
        
        headers = {"Content-Type": "application/json"}
        data = json.dumps(order_data)
        
        return await self.make_request("POST", url, headers=headers, data=data)

    async def run_mixed_load(self, duration: int = 60, concurrent_requests: int = 5):
        """Run mixed load test for specified duration."""
        print(f"Starting load test for {duration} seconds with {concurrent_requests} concurrent requests")
        print(f"Targeting: {self.base_url}")
        print("-" * 60)
        
        start_time = time.time()
        tasks = []
        
        async def worker():
            while time.time() - start_time < duration:
                # Weighted random selection of test types
                test_weights = [
                    (self.test_health_check, 10),    # 10% health checks
                    (self.test_users_list, 25),      # 25% user requests
                    (self.test_products_list, 30),   # 30% product lists
                    (self.test_product_search, 25),  # 25% product searches
                    (self.test_complete_order_flow, 10)  # 10% complete orders
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
    
    # Test configuration
    duration = 60  # seconds
    concurrent_requests = 5
    
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