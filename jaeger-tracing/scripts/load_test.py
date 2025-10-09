#!/usr/bin/env python3
"""Load testing script for FastAPI Jaeger tracing demo."""

import asyncio
import random
import time
import statistics
from typing import List, Dict, Any
import httpx
import argparse
from datetime import datetime
from dataclasses import dataclass


@dataclass
class RequestResult:
    """Result of a single request."""
    url: str
    method: str
    status_code: int
    response_time: float
    error: str = None


class LoadTester:
    """Advanced load testing with detailed metrics."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.results: List[RequestResult] = []
    
    async def run_load_test(
        self,
        concurrent_users: int = 10,
        requests_per_user: int = 50,
        ramp_up_time: int = 10
    ) -> Dict[str, Any]:
        """Run a comprehensive load test."""
        print(f"Starting load test...")
        print(f"   Concurrent users: {concurrent_users}")
        print(f"   Requests per user: {requests_per_user}")
        print(f"   Ramp-up time: {ramp_up_time}s")
        print()
        
        start_time = time.time()
        
        # Create tasks for concurrent users
        user_delay = ramp_up_time / concurrent_users if concurrent_users > 1 else 0
        tasks = []
        
        for user_id in range(concurrent_users):
            delay = user_id * user_delay
            task = asyncio.create_task(
                self._simulate_user(user_id, requests_per_user, delay)
            )
            tasks.append(task)
        
        # Wait for all users to complete
        await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        # Calculate metrics
        metrics = self._calculate_metrics(total_time)
        self._print_metrics(metrics)
        
        return metrics
    
    async def _simulate_user(self, user_id: int, requests: int, delay: float) -> None:
        """Simulate a single user's behavior."""
        if delay > 0:
            await asyncio.sleep(delay)
        
        timeout = httpx.Timeout(30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            for i in range(requests):
                await self._make_request(client, user_id, i)
                # Random think time between requests
                await asyncio.sleep(random.uniform(0.1, 2.0))
    
    async def _make_request(self, client: httpx.AsyncClient, user_id: int, request_id: int) -> None:
        """Make a single request and record the result."""
        # Choose request type based on realistic distribution
        request_type = random.choices(
            ["health", "get_user", "create_order", "demo_flow", "error"],
            weights=[10, 30, 25, 30, 5],
            k=1
        )[0]
        
        start_time = time.time()
        result = None
        
        try:
            if request_type == "health":
                response = await client.get(f"{self.base_url}/health")
                result = RequestResult(
                    url="/health",
                    method="GET",
                    status_code=response.status_code,
                    response_time=time.time() - start_time
                )
            
            elif request_type == "get_user":
                user_id_param = random.randint(1, 3)
                response = await client.get(f"{self.base_url}/users/{user_id_param}")
                result = RequestResult(
                    url=f"/users/{user_id_param}",
                    method="GET",
                    status_code=response.status_code,
                    response_time=time.time() - start_time
                )
            
            elif request_type == "create_order":
                order_data = {
                    "user_id": random.randint(1, 3),
                    "amount": round(random.uniform(10.0, 200.0), 2),
                    "items": [f"item_{i}" for i in range(random.randint(1, 3))]
                }
                response = await client.post(f"{self.base_url}/orders", json=order_data)
                result = RequestResult(
                    url="/orders",
                    method="POST",
                    status_code=response.status_code,
                    response_time=time.time() - start_time
                )
            
            elif request_type == "demo_flow":
                user_id_param = random.randint(1, 3)
                response = await client.get(f"{self.base_url}/demo/full-flow/{user_id_param}")
                result = RequestResult(
                    url=f"/demo/full-flow/{user_id_param}",
                    method="GET",
                    status_code=response.status_code,
                    response_time=time.time() - start_time
                )
            
            elif request_type == "error":
                # Intentionally cause an error
                response = await client.get(f"{self.base_url}/users/999")
                result = RequestResult(
                    url="/users/999",
                    method="GET",
                    status_code=response.status_code,
                    response_time=time.time() - start_time
                )
        
        except httpx.HTTPStatusError as e:
            result = RequestResult(
                url=str(e.request.url),
                method=e.request.method,
                status_code=e.response.status_code,
                response_time=time.time() - start_time,
                error=f"HTTP {e.response.status_code}"
            )
        
        except Exception as e:
            result = RequestResult(
                url="unknown",
                method="unknown",
                status_code=0,
                response_time=time.time() - start_time,
                error=str(e)
            )
        
        if result:
            self.results.append(result)
    
    def _calculate_metrics(self, total_time: float) -> Dict[str, Any]:
        """Calculate performance metrics."""
        if not self.results:
            return {"error": "No results to analyze"}
        
        # Response times
        response_times = [r.response_time for r in self.results]
        
        # Status codes
        status_codes = {}
        errors = []
        
        for result in self.results:
            status_codes[result.status_code] = status_codes.get(result.status_code, 0) + 1
            if result.error:
                errors.append(result.error)
        
        # Calculate percentiles
        response_times.sort()
        n = len(response_times)
        
        metrics = {
            "total_requests": len(self.results),
            "total_time": total_time,
            "requests_per_second": len(self.results) / total_time,
            "response_times": {
                "min": min(response_times),
                "max": max(response_times),
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "p95": response_times[int(n * 0.95)] if n > 0 else 0,
                "p99": response_times[int(n * 0.99)] if n > 0 else 0,
            },
            "status_codes": status_codes,
            "error_rate": len([r for r in self.results if r.status_code >= 400]) / len(self.results) * 100,
            "errors": list(set(errors)),
        }
        
        return metrics
    
    def _print_metrics(self, metrics: Dict[str, Any]) -> None:
        """Print formatted metrics."""
        print("Load Test Results")
        print("=" * 50)
        print(f"Total Requests:      {metrics['total_requests']}")
        print(f"Total Time:          {metrics['total_time']:.2f}s")
        print(f"Requests/sec:        {metrics['requests_per_second']:.2f}")
        print(f"Error Rate:          {metrics['error_rate']:.2f}%")
        print()
        
        print("Response Times (seconds)")
        print("-" * 30)
        rt = metrics['response_times']
        print(f"Min:                 {rt['min']:.3f}s")
        print(f"Max:                 {rt['max']:.3f}s")
        print(f"Mean:                {rt['mean']:.3f}s")
        print(f"Median:              {rt['median']:.3f}s")
        print(f"95th percentile:     {rt['p95']:.3f}s")
        print(f"99th percentile:     {rt['p99']:.3f}s")
        print()
        
        print("Status Code Distribution")
        print("-" * 30)
        for status, count in sorted(metrics['status_codes'].items()):
            percentage = count / metrics['total_requests'] * 100
            print(f"{status}:                  {count} ({percentage:.1f}%)")
        
        if metrics['errors']:
            print()
            print("Errors Encountered")
            print("-" * 30)
            for error in metrics['errors'][:10]:  # Show first 10 unique errors
                print(f"  • {error}")


async def main():
    parser = argparse.ArgumentParser(description="FastAPI Load Testing Tool")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the FastAPI application")
    parser.add_argument("--users", type=int, default=10, help="Number of concurrent users")
    parser.add_argument("--requests", type=int, default=50, help="Requests per user")
    parser.add_argument("--ramp-up", type=int, default=10, help="Ramp-up time in seconds")
    
    args = parser.parse_args()
    
    print(f"FastAPI Load Testing Tool")
    print(f"   Target URL: {args.url}")
    print(f"   Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test connection first
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{args.url}/health")
            print(f"Connection test successful (Status: {response.status_code})")
    except Exception as e:
        print(f"Failed to connect to {args.url}: {e}")
        return
    
    print()
    
    # Run load test
    tester = LoadTester(args.url)
    metrics = await tester.run_load_test(
        concurrent_users=args.users,
        requests_per_user=args.requests,
        ramp_up_time=args.ramp_up
    )
    
    print()
    print("Load test completed!")
    print(f"   Check Jaeger UI at: http://localhost:16686")
    print(f"   Look for performance traces and bottlenecks")


if __name__ == "__main__":
    asyncio.run(main())