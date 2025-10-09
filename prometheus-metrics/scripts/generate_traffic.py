#!/usr/bin/env python3
"""
Traffic generation script for FastAPI Prometheus metrics testing.
Generates various types of traffic patterns to test monitoring setup.
"""

import asyncio
import random
import time
from typing import List
import aiohttp
import argparse
import sys


class TrafficGenerator:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.endpoints = [
            "/health/",
            "/api/v1/users/",
            "/api/v1/items/",
            "/metrics",
        ]
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, endpoint: str) -> bool:
        """Make a single request and return success status."""
        try:
            url = f"{self.base_url}{endpoint}"
            async with self.session.get(url, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False
    
    async def generate_steady_traffic(self, duration: int, requests_per_second: float):
        """Generate steady traffic at specified rate."""
        print(f"Generating steady traffic: {requests_per_second} req/sec for {duration} seconds")
        
        interval = 1.0 / requests_per_second
        end_time = time.time() + duration
        request_count = 0
        success_count = 0
        
        while time.time() < end_time:
            endpoint = random.choice(self.endpoints)
            success = await self.make_request(endpoint)
            
            request_count += 1
            if success:
                success_count += 1
            
            if request_count % 10 == 0:
                remaining = int(end_time - time.time())
                success_rate = (success_count / request_count) * 100
                print(f"Requests: {request_count}, Success: {success_rate:.1f}%, Remaining: {remaining}s")
            
            await asyncio.sleep(interval)
        
        success_rate = (success_count / request_count) * 100
        print(f"Completed: {request_count} requests, {success_rate:.1f}% success rate")
    
    async def generate_burst_traffic(self, bursts: int, burst_size: int, burst_interval: float):
        """Generate traffic in bursts."""
        print(f"Generating burst traffic: {bursts} bursts of {burst_size} requests each")
        
        total_requests = 0
        total_success = 0
        
        for burst_num in range(bursts):
            print(f"Starting burst {burst_num + 1}/{bursts}")
            
            # Create concurrent requests for this burst
            tasks = []
            for _ in range(burst_size):
                endpoint = random.choice(self.endpoints)
                tasks.append(self.make_request(endpoint))
            
            # Execute burst
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successes
            burst_success = sum(1 for r in results if r is True)
            total_requests += burst_size
            total_success += burst_success
            
            print(f"Burst {burst_num + 1} completed: {burst_success}/{burst_size} successful")
            
            # Wait before next burst (except for last burst)
            if burst_num < bursts - 1:
                await asyncio.sleep(burst_interval)
        
        success_rate = (total_success / total_requests) * 100
        print(f"All bursts completed: {total_requests} total requests, {success_rate:.1f}% success rate")
    
    async def generate_random_traffic(self, duration: int, min_interval: float, max_interval: float):
        """Generate random traffic with variable intervals."""
        print(f"Generating random traffic for {duration} seconds")
        
        end_time = time.time() + duration
        request_count = 0
        success_count = 0
        
        while time.time() < end_time:
            endpoint = random.choice(self.endpoints)
            success = await self.make_request(endpoint)
            
            request_count += 1
            if success:
                success_count += 1
            
            if request_count % 5 == 0:
                remaining = int(end_time - time.time())
                success_rate = (success_count / request_count) * 100 if request_count > 0 else 0
                print(f"Random traffic: {request_count} requests, {success_rate:.1f}% success, {remaining}s remaining")
            
            # Random interval between requests
            interval = random.uniform(min_interval, max_interval)
            await asyncio.sleep(interval)
        
        success_rate = (success_count / request_count) * 100 if request_count > 0 else 0
        print(f"Random traffic completed: {request_count} requests, {success_rate:.1f}% success rate")


async def main():
    parser = argparse.ArgumentParser(description="Generate traffic for FastAPI metrics testing")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for the application")
    
    subparsers = parser.add_subparsers(dest="mode", help="Traffic generation mode")
    
    # Steady traffic
    steady = subparsers.add_parser("steady", help="Generate steady traffic")
    steady.add_argument("--duration", type=int, default=60, help="Duration in seconds")
    steady.add_argument("--rate", type=float, default=1.0, help="Requests per second")
    
    # Burst traffic
    burst = subparsers.add_parser("burst", help="Generate burst traffic")
    burst.add_argument("--bursts", type=int, default=5, help="Number of bursts")
    burst.add_argument("--size", type=int, default=10, help="Requests per burst")
    burst.add_argument("--interval", type=float, default=5.0, help="Seconds between bursts")
    
    # Random traffic
    random_parser = subparsers.add_parser("random", help="Generate random traffic")
    random_parser.add_argument("--duration", type=int, default=60, help="Duration in seconds")
    random_parser.add_argument("--min-interval", type=float, default=0.1, help="Minimum interval between requests")
    random_parser.add_argument("--max-interval", type=float, default=2.0, help="Maximum interval between requests")
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        return
    
    async with TrafficGenerator(args.url) as generator:
        if args.mode == "steady":
            await generator.generate_steady_traffic(args.duration, args.rate)
        elif args.mode == "burst":
            await generator.generate_burst_traffic(args.bursts, args.size, args.interval)
        elif args.mode == "random":
            await generator.generate_random_traffic(args.duration, args.min_interval, args.max_interval)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTraffic generation stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)