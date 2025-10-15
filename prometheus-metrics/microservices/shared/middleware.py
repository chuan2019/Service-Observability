"""Prometheus metrics middleware for FastAPI applications."""

import time

from fastapi import Request
from prometheus_client import REGISTRY, Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

# HTTP Request metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code", "service"],
    registry=REGISTRY,
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "service"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint", "service"],
    registry=REGISTRY,
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP requests with Prometheus metrics."""

    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next):
        """Process HTTP request and record metrics."""

        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Get route path for better grouping (instead of actual URL with IDs)
        endpoint = request.url.path
        for route in request.app.routes:
            match, child_scope = route.matches(request.scope)
            if match:
                endpoint = route.path
                break

        method = request.method

        # Track request in progress
        HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint, service=self.service_name).inc()

        # Track request duration
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code

            # Record metrics
            HTTP_REQUESTS_TOTAL.labels(
                method=method, endpoint=endpoint, status_code=status_code, service=self.service_name
            ).inc()

            duration = time.time() - start_time
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint, service=self.service_name).observe(
                duration
            )

            return response

        except Exception as e:
            # Record error metrics
            HTTP_REQUESTS_TOTAL.labels(
                method=method, endpoint=endpoint, status_code=500, service=self.service_name
            ).inc()

            duration = time.time() - start_time
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=endpoint, service=self.service_name).observe(
                duration
            )

            raise e

        finally:
            # Decrement in-progress counter
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method, endpoint=endpoint, service=self.service_name).dec()
