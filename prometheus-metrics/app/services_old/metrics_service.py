"""
Metrics service for custom business metrics.
"""

from typing import Dict, Optional
from prometheus_client import Counter, Histogram, Gauge
from app.middleware.metrics import REGISTRY


# Global metrics instances to avoid duplication
_USER_OPERATIONS = None
_TASK_METRICS = None
_PROCESSING_TIME = None
_ACTIVE_SESSIONS = None
_MEMORY_USAGE = None
_API_ERRORS = None


class MetricsService:
    """Service for managing custom application metrics."""
    
    def __init__(self):
        # Custom counters
        self.custom_counters: Dict[str, Counter] = {}
        self.custom_histograms: Dict[str, Histogram] = {}
        self.custom_gauges: Dict[str, Gauge] = {}
        
        # Initialize some common business metrics
        self._init_business_metrics()
    
    def _init_business_metrics(self):
        """Initialize common business metrics."""
        global _USER_OPERATIONS, _TASK_METRICS, _PROCESSING_TIME, _ACTIVE_SESSIONS, _MEMORY_USAGE, _API_ERRORS
        
        # User-related metrics
        if _USER_OPERATIONS is None:
            _USER_OPERATIONS = Counter(
                'user_operations_total',
                'Total number of user operations',
                ['operation', 'status'],
                registry=REGISTRY
            )
        self.user_operations = _USER_OPERATIONS
        
        # Task-related metrics
        if _TASK_METRICS is None:
            _TASK_METRICS = Counter(
                'task_operations_total',
                'Total number of task operations',
                ['operation'],
                registry=REGISTRY
            )
        self.task_metrics = _TASK_METRICS
        
        # Processing time metrics
        if _PROCESSING_TIME is None:
            _PROCESSING_TIME = Histogram(
                'business_processing_seconds',
                'Time spent on business operations',
                ['operation'],
                registry=REGISTRY
            )
        self.processing_time = _PROCESSING_TIME
        
        # Active connections/sessions
        if _ACTIVE_SESSIONS is None:
            _ACTIVE_SESSIONS = Gauge(
                'active_sessions',
                'Number of active user sessions',
                registry=REGISTRY
            )
        self.active_sessions = _ACTIVE_SESSIONS
        
        # Memory usage metrics
        if _MEMORY_USAGE is None:
            _MEMORY_USAGE = Gauge(
                'memory_usage_bytes',
                'Current memory usage in bytes',
                ['component'],
                registry=REGISTRY
            )
        self.memory_usage = _MEMORY_USAGE
        
        # Custom application metrics
        if _API_ERRORS is None:
            _API_ERRORS = Counter(
                'api_errors_total',
                'Total number of API errors',
                ['endpoint', 'error_type'],
                registry=REGISTRY
            )
        self.api_errors = _API_ERRORS
    
    def increment_counter(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Increment a custom counter."""
        if name == "api_users_requested":
            self.user_operations.labels(operation="get_users", status="success").inc()
        elif name == "api_user_requested":
            self.user_operations.labels(operation="get_user", status="success").inc()
        elif name == "api_users_created":
            self.user_operations.labels(operation="create_user", status="success").inc()
        elif name == "api_errors_total":
            if labels:
                self.api_errors.labels(**labels).inc()
        elif name == "tasks_created":
            self.task_metrics.labels(operation="created").inc()
        elif name == "tasks_completed":
            self.task_metrics.labels(operation="completed").inc()
        elif name == "tasks_failed":
            self.task_metrics.labels(operation="failed").inc()
        elif name == "api_slow_requests":
            self.task_metrics.labels(operation="slow_request").inc()
        elif name == "api_memory_intensive_requests":
            self.task_metrics.labels(operation="memory_intensive").inc()
        else:
            # Create a new counter if it doesn't exist
            if name not in self.custom_counters:
                self.custom_counters[name] = Counter(
                    name,
                    f'Custom counter: {name}',
                    list(labels.keys()) if labels else [],
                    registry=REGISTRY
                )
            
            if labels:
                self.custom_counters[name].labels(**labels).inc()
            else:
                self.custom_counters[name].inc()
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Observe a value in a histogram."""
        if name not in self.custom_histograms:
            self.custom_histograms[name] = Histogram(
                name,
                f'Custom histogram: {name}',
                list(labels.keys()) if labels else [],
                registry=REGISTRY
            )
        
        if labels:
            self.custom_histograms[name].labels(**labels).observe(value)
        else:
            self.custom_histograms[name].observe(value)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge value."""
        if name not in self.custom_gauges:
            self.custom_gauges[name] = Gauge(
                name,
                f'Custom gauge: {name}',
                list(labels.keys()) if labels else [],
                registry=REGISTRY
            )
        
        if labels:
            self.custom_gauges[name].labels(**labels).set(value)
        else:
            self.custom_gauges[name].set(value)
    
    def increment_gauge(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Increment a gauge."""
        if name not in self.custom_gauges:
            self.custom_gauges[name] = Gauge(
                name,
                f'Custom gauge: {name}',
                list(labels.keys()) if labels else [],
                registry=REGISTRY
            )
        
        if labels:
            self.custom_gauges[name].labels(**labels).inc()
        else:
            self.custom_gauges[name].inc()
    
    def decrement_gauge(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Decrement a gauge."""
        if name not in self.custom_gauges:
            self.custom_gauges[name] = Gauge(
                name,
                f'Custom gauge: {name}',
                list(labels.keys()) if labels else [],
                registry=REGISTRY
            )
        
        if labels:
            self.custom_gauges[name].labels(**labels).dec()
        else:
            self.custom_gauges[name].dec()