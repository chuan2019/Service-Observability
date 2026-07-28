import base64
import logging
import os

from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource

# --- Traces ---
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# --- Metrics ---
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

# --- Logs ---
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# ---------------------------------------------------------------- config ---
OO_BASE = os.getenv("OO_BASE", "http://localhost:5080/api/default")
OO_USER = os.getenv("OO_USER", "root@example.com")
OO_PASS = os.getenv("OO_PASS", "Complexpass#123")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "fastapi-demo")

_token = base64.b64encode(f"{OO_USER}:{OO_PASS}".encode()).decode()
HEADERS = {"Authorization": f"Basic {_token}"}

RESOURCE = Resource.create({
    "service.name": SERVICE_NAME,
    "service.version": "1.0.0",
    "deployment.environment": os.getenv("APP_ENV", "dev"),
})


def setup_telemetry(app) -> None:
    """Configure traces, metrics and logs, then instrument the app."""

    # ------------------------------------------------------------ traces --
    tracer_provider = TracerProvider(resource=RESOURCE)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=f"{OO_BASE}/v1/traces", headers=HEADERS)
        )
    )
    trace.set_tracer_provider(tracer_provider)

    # ----------------------------------------------------------- metrics --
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{OO_BASE}/v1/metrics", headers=HEADERS),
        export_interval_millis=10_000,
    )
    metrics.set_meter_provider(
        MeterProvider(resource=RESOURCE, metric_readers=[reader])
    )

    # -------------------------------------------------------------- logs --
    logger_provider = LoggerProvider(resource=RESOURCE)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(
                endpoint=f"{OO_BASE}/v1/logs",
                # optional: route to a named stream instead of "default"
                headers={**HEADERS, "stream-name": "fastapi_logs"},
            )
        )
    )
    set_logger_provider(logger_provider)

    # Bridge stdlib logging -> OTel logs, and stamp trace/span IDs on records
    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.INFO)
    LoggingInstrumentor().instrument(set_logging_format=True)

    # -------------------------------------------- FastAPI instrumentation --
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=tracer_provider,
        excluded_urls="healthz",   # don't trace health checks
    )
