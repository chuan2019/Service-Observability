"""Configuration package for the FastAPI Jaeger tracing application."""

from .tracing import TracingConfig, get_tracer, instrument_fastapi, setup_tracing

__all__ = ["TracingConfig", "setup_tracing", "instrument_fastapi", "get_tracer"]
