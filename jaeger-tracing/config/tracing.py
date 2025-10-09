"""Configuration for OpenTelemetry and Jaeger tracing."""

import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class TracingConfig:
    """Configuration class for OpenTelemetry tracing."""
    
    def __init__(
        self,
        service_name: str = "fastapi-jaeger-demo",
        otlp_endpoint: str = "http://localhost:4318/v1/traces",
        environment: str = "development",
    ):
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint
        self.environment = environment
        
    @classmethod
    def from_env(cls) -> "TracingConfig":
        """Create configuration from environment variables."""
        jaeger_host = os.getenv("JAEGER_HOST", "localhost")
        otlp_endpoint = f"http://{jaeger_host}:4318/v1/traces"
        
        return cls(
            service_name=os.getenv("SERVICE_NAME", "fastapi-jaeger-demo"),
            otlp_endpoint=os.getenv("OTLP_ENDPOINT", otlp_endpoint),
            environment=os.getenv("ENVIRONMENT", "development"),
        )


def setup_tracing(config: Optional[TracingConfig] = None) -> None:
    """Set up OpenTelemetry tracing with Jaeger exporter."""
    if config is None:
        config = TracingConfig.from_env()
    
    # Create resource with service information
    resource = Resource.create({
        "service.name": config.service_name,
        "service.version": "1.0.0",
        "deployment.environment": config.environment,
    })
    
    # Set up tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # Create OTLP exporter for Jaeger
    otlp_exporter = OTLPSpanExporter(
        endpoint=config.otlp_endpoint,
        headers={}
    )
    
    # Add span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
    
    # Instrument libraries
    RequestsInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
    
    print(f"Tracing configured for service: {config.service_name}")
    print(f"OTLP endpoint: {config.otlp_endpoint}")


def instrument_fastapi(app) -> None:
    """Instrument FastAPI application with OpenTelemetry."""
    FastAPIInstrumentor.instrument_app(app)
    print("FastAPI instrumented with OpenTelemetry")


def get_tracer(name: str = __name__) -> trace.Tracer:
    """Get a tracer instance."""
    return trace.get_tracer(name)