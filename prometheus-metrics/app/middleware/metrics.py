"""
Prometheus metrics middleware for FastAPI.
"""

import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from starlette.middleware.base import BaseHTTPMiddleware

# Create custom registry for application metrics
REGISTRY = CollectorRegistry()

# HTTP request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=REGISTRY
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=REGISTRY
)

REQUEST_SIZE = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint'],
    registry=REGISTRY
)

RESPONSE_SIZE = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint'],
    registry=REGISTRY
)

# Application metrics
ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests',
    registry=REGISTRY
)

# Custom business metrics
BUSINESS_OPERATIONS = Counter(
    'business_operations_total',
    'Total number of business operations',
    ['operation_type', 'status'],
    registry=REGISTRY
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics collection for the metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        # Get request info
        method = request.method
        path_template = self._get_path_template(request)
        
        # Increment active requests
        ACTIVE_REQUESTS.inc()
        
        # Record request size
        request_size = int(request.headers.get('content-length', 0))
        REQUEST_SIZE.labels(method=method, endpoint=path_template).observe(request_size)
        
        # Start timing
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            status_code = str(response.status_code)
            REQUEST_COUNT.labels(method=method, endpoint=path_template, status_code=status_code).inc()
            REQUEST_DURATION.labels(method=method, endpoint=path_template).observe(duration)
            
            # Record response size
            response_size = int(response.headers.get('content-length', 0))
            RESPONSE_SIZE.labels(method=method, endpoint=path_template).observe(response_size)
            
            return response
            
        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            REQUEST_COUNT.labels(method=method, endpoint=path_template, status_code="500").inc()
            REQUEST_DURATION.labels(method=method, endpoint=path_template).observe(duration)
            raise e
            
        finally:
            # Decrement active requests
            ACTIVE_REQUESTS.dec()

    def _get_path_template(self, request: Request) -> str:
        """Extract path template from request."""
        # Try to get the route pattern
        if hasattr(request, 'scope') and 'route' in request.scope:
            route = request.scope['route']
            if hasattr(route, 'path'):
                return route.path
        
        # Fallback to actual path, but normalize path parameters
        path = request.url.path
        
        # Simple normalization for common patterns
        import re
        
        # Replace numeric IDs with {id}
        path = re.sub(r'/\d+', '/{id}', path)
        
        # Replace UUIDs with {uuid}
        path = re.sub(r'/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '/{uuid}', path)
        
        return path