#!/usr/bin/env python3
"""
Real-time monitoring script for FastAPI Prometheus metrics.
Displays key metrics in a dashboard-like format.
"""

import asyncio
import aiohttp
import sys
from datetime import datetime
from typing import Dict, Any
import argparse


class MetricsMonitor:
    def __init__(self, app_url: str = "http://localhost:8000", prometheus_url: str = "http://localhost:9090"):
        self.app_url = app_url.rstrip('/')
        self.prometheus_url = prometheus_url.rstrip('/')
        self.session = None

        # Microservices endpoints
        self.services = {
            "user": "http://localhost:8001",
            "product": "http://localhost:8002",
            "inventory": "http://localhost:8003",
            "order": "http://localhost:8004",
            "payment": "http://localhost:8005",
            "notification": "http://localhost:8006",
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_app_health(self) -> Dict[str, Any]:
        """Get health status of all microservices."""
        health_results = {}

        for service_name, service_url in self.services.items():
            try:
                async with self.session.get(f"{service_url}/health", timeout=5) as response:
                    if response.status == 200:
                        # Use text() first to avoid mimetype issues
                        text = await response.text()
                        try:
                            import json
                            health_results[service_name] = json.loads(text)
                        except:
                            health_results[service_name] = {"status": "healthy", "raw": text}
                    else:
                        health_results[service_name] = {"status": "unhealthy", "reason": f"HTTP {response.status}"}
            except Exception as e:
                health_results[service_name] = {"status": "error", "reason": str(e)}

        # Overall health
        all_healthy = all(
            h.get("status") in ["healthy", "ok"]
            for h in health_results.values()
        )

        return {
            "overall_status": "healthy" if all_healthy else "degraded",
            "services": health_results,
            "timestamp": datetime.now().isoformat()
        }

    async def get_app_metrics(self) -> Dict[str, Any]:
        """Get raw metrics from all microservices."""
        metrics_results = {}

        for service_name, service_url in self.services.items():
            try:
                async with self.session.get(f"{service_url}/metrics", timeout=5) as response:
                    if response.status == 200:
                        metrics_results[service_name] = {
                            "status": "ok",
                            "data": await response.text()
                        }
                    else:
                        metrics_results[service_name] = {
                            "status": "error",
                            "data": f"HTTP {response.status}"
                        }
            except Exception as e:
                metrics_results[service_name] = {
                    "status": "error",
                    "data": str(e)
                }

        return metrics_results

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
                        # Aggregate metrics with same name
                        if clean_name in parsed:
                            parsed[clean_name] += float(value)
                        else:
                            parsed[clean_name] = float(value)
                except (ValueError, IndexError):
                    continue
        return parsed

    def parse_all_service_metrics(self, all_metrics: Dict[str, Dict]) -> Dict[str, float]:
        """Parse metrics from all services and aggregate."""
        aggregated = {}

        for service_name, metrics_data in all_metrics.items():
            if metrics_data.get("status") == "ok":
                service_metrics = self.parse_prometheus_metrics(metrics_data["data"])
                # Add service metrics to aggregated with service prefix
                for metric_name, value in service_metrics.items():
                    # Aggregate same metrics across services
                    if metric_name in aggregated:
                        aggregated[metric_name] += value
                    else:
                        aggregated[metric_name] = value

        return aggregated

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
            avg_duration = duration_metrics['http_request_duration_seconds_sum'] / \
                duration_metrics['http_request_duration_seconds_count']
            summary.append(f"Avg Request Duration: {avg_duration*1000:.2f} ms")

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
                print(f"Overall Status: {health.get('overall_status', 'unknown')}")
                print("\nService Health:")
                for service_name, service_health in health.get('services', {}).items():
                    status = service_health.get('status', 'unknown')
                    status_symbol = "*" if status in ['healthy', 'ok'] else "x"
                    print(f"  {status_symbol} {service_name}: {status}")
                print()

                # Metrics
                all_metrics = await self.get_app_metrics()
                parsed_metrics = self.parse_all_service_metrics(all_metrics)

                if parsed_metrics:
                    print("Aggregated Metrics Across All Services:")
                    print("-" * 40)
                    print(self.format_metrics_summary(parsed_metrics))

                    print("\nMetrics Summary:")
                    print(f"Total unique metrics: {len(parsed_metrics)}")
                    services_ok = sum(1 for m in all_metrics.values() if m.get('status') == 'ok')
                    print(f"Services reporting metrics: {services_ok}/{len(self.services)}")
                else:
                    print("No metrics available from services")

                print("\n" + "=" * 60)
                print(f"Refreshing in {refresh_interval} seconds... (Ctrl+C to stop)")

                await asyncio.sleep(refresh_interval)

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")

    async def show_current_metrics(self):
        """Show current metrics once."""
        print("Current FastAPI Microservices Metrics")
        print("=" * 50)

        # Health check
        health = await self.get_app_health()
        print(f"\nOverall Status: {health.get('overall_status', 'unknown')}")
        print("\nService Health:")
        for service_name, service_health in health.get('services', {}).items():
            status = service_health.get('status', 'unknown')
            status_symbol = "*" if status in ['healthy', 'ok'] else "x"
            print(f"  {status_symbol} {service_name}: {status}")
        print()

        # Metrics
        all_metrics = await self.get_app_metrics()
        parsed_metrics = self.parse_all_service_metrics(all_metrics)

        if parsed_metrics:
            print("Aggregated Metrics Summary:")
            print(self.format_metrics_summary(parsed_metrics))
            print(f"\nTotal unique metrics: {len(parsed_metrics)}")
            services_ok = sum(1 for m in all_metrics.values() if m.get('status') == 'ok')
            print(f"Services reporting metrics: {services_ok}/{len(self.services)}")
        else:
            print("No metrics available from services")
            for service_name, metrics_data in all_metrics.items():
                if metrics_data.get('status') == 'error':
                    print(f"  Error from {service_name}: {metrics_data.get('data', 'unknown error')}")


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