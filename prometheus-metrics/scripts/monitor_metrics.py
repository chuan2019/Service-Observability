#!/usr/bin/env python3
"""
Real-time monitoring script for FastAPI Prometheus metrics.
Displays key metrics in a dashboard-like format.
"""

import asyncio
import aiohttp
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any
import argparse


class MetricsMonitor:
    def __init__(self, app_url: str = "http://localhost:8000", prometheus_url: str = "http://localhost:9090"):
        self.app_url = app_url
        self.prometheus_url = prometheus_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_app_health(self) -> Dict[str, Any]:
        """Get application health status."""
        try:
            async with self.session.get(f"{self.app_url}/health/", timeout=5) as response:
                if response.status == 200:
                    return await response.json()
                return {"status": "unhealthy", "reason": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    async def get_app_metrics(self) -> Dict[str, str]:
        """Get raw metrics from the application."""
        try:
            async with self.session.get(f"{self.app_url}/metrics", timeout=5) as response:
                if response.status == 200:
                    return {"status": "ok", "data": await response.text()}
                return {"status": "error", "data": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "data": str(e)}
    
    def parse_prometheus_metrics(self, metrics_text: str) -> Dict[str, float]:
        """Parse Prometheus metrics text format."""
        parsed = {}
        for line in metrics_text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    if ' ' in line:
                        name, value = line.rsplit(' ', 1)
                        # Clean up metric name (remove labels for display)
                        clean_name = name.split('{')[0]
                        parsed[clean_name] = float(value)
                except (ValueError, IndexError):
                    continue
        return parsed
    
    def format_metrics_summary(self, metrics: Dict[str, float]) -> str:
        """Format metrics into a readable summary."""
        summary = []
        
        # HTTP metrics
        http_requests = {k: v for k, v in metrics.items() if 'http_requests_total' in k}
        if http_requests:
            total_requests = sum(http_requests.values())
            summary.append(f"Total HTTP Requests: {total_requests:.0f}")
        
        # Request duration
        duration_metrics = {k: v for k, v in metrics.items() if 'http_request_duration' in k}
        if duration_metrics:
            avg_duration = sum(duration_metrics.values()) / len(duration_metrics)
            summary.append(f"Avg Request Duration: {avg_duration:.3f}s")
        
        # Business metrics
        business_metrics = {k: v for k, v in metrics.items() if 'business_metric' in k}
        if business_metrics:
            for name, value in business_metrics.items():
                summary.append(f"Business Metric: {value:.2f}")
        
        # User metrics
        user_metrics = {k: v for k, v in metrics.items() if 'user_active' in k}
        if user_metrics:
            for name, value in user_metrics.items():
                summary.append(f"Active Users: {value:.0f}")
        
        return '\n'.join(summary) if summary else "No metrics available"
    
    async def display_dashboard(self, refresh_interval: int = 5):
        """Display a real-time dashboard."""
        print("FastAPI Prometheus Metrics Monitor")
        print("=" * 50)
        print("Press Ctrl+C to stop")
        print()
        
        try:
            while True:
                # Clear screen (works on most terminals)
                print("\033[2J\033[H", end="")
                
                # Header
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"FastAPI Metrics Dashboard - {timestamp}")
                print("=" * 60)
                
                # Application Health
                health = await self.get_app_health()
                print(f"Application Status: {health.get('status', 'unknown')}")
                if health.get('reason'):
                    print(f"Reason: {health['reason']}")
                print()
                
                # Metrics
                metrics_response = await self.get_app_metrics()
                if metrics_response['status'] == 'ok':
                    parsed_metrics = self.parse_prometheus_metrics(metrics_response['data'])
                    print("Key Metrics:")
                    print("-" * 20)
                    print(self.format_metrics_summary(parsed_metrics))
                    
                    print("\nRaw Metrics Count:")
                    print(f"Total metrics collected: {len(parsed_metrics)}")
                else:
                    print("Metrics Error:")
                    print(metrics_response['data'])
                
                print("\n" + "=" * 60)
                print(f"Refreshing in {refresh_interval} seconds... (Ctrl+C to stop)")
                
                await asyncio.sleep(refresh_interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
    
    async def show_current_metrics(self):
        """Show current metrics once."""
        print("Current FastAPI Metrics")
        print("=" * 30)
        
        # Health check
        health = await self.get_app_health()
        print(f"Health: {health}")
        print()
        
        # Metrics
        metrics_response = await self.get_app_metrics()
        if metrics_response['status'] == 'ok':
            parsed_metrics = self.parse_prometheus_metrics(metrics_response['data'])
            print("Parsed Metrics Summary:")
            print(self.format_metrics_summary(parsed_metrics))
            print(f"\nTotal metrics: {len(parsed_metrics)}")
        else:
            print(f"Error getting metrics: {metrics_response['data']}")


async def main():
    parser = argparse.ArgumentParser(description="Monitor FastAPI Prometheus metrics")
    parser.add_argument("--app-url", default="http://localhost:8000", help="FastAPI application URL")
    parser.add_argument("--prometheus-url", default="http://localhost:9090", help="Prometheus URL")
    parser.add_argument("--refresh", type=int, default=5, help="Refresh interval for dashboard (seconds)")
    parser.add_argument("--once", action="store_true", help="Show metrics once instead of continuous monitoring")
    
    args = parser.parse_args()
    
    async with MetricsMonitor(args.app_url, args.prometheus_url) as monitor:
        if args.once:
            await monitor.show_current_metrics()
        else:
            await monitor.display_dashboard(args.refresh)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)