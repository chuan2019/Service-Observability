import logging
import random
import time

from fastapi import FastAPI, HTTPException
from opentelemetry import trace, metrics

from telemetry import setup_telemetry


app = FastAPI(title="FastAPI + OpenObserve demo")
setup_telemetry(app)  # must run after app is created

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)
meter  = metrics.get_meter(__name__)

# ------ custom metrics --------------------------------------------------
order_counter = meter.create_counter(
    "orders_created", unit="1", description="Number of orders created"
)

checkout_duration = meter.create_histogram(
    "checkout_duration_ms", unit="ms", description="Checkout latency"
)


# ----- routes ---------------------------------------------------------
@app.get("/healthz")
async def healthz():   # excluded from tracing
    return {"status": "ok"}

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Hello from FastAPI + OpenObserve"}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    logger.info("Fetching item %s", item_id)
    if item_id == 13:
        logger.error("Unlucky item requested: %s", item_id)
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id}

@app.post("/orders")
async def create_order():
    # custom child span with attributes + events
    with tracer.start_as_current_span("process-order") as span:
        span.set_attribute("order.channel", "web")
        start = time.perf_counter()

        with tracer.start_as_current_span("validate-payment"):
            time.sleep(random.uniform(0.01, 0.05))  # simulated work

        with tracer.start_as_current_span("reserve-inventory"):
            time.sleep(random.uniform(0.01, 0.08))  # simulated work

        elapsed_ms = (time.perf_counter() - start) * 1000
        order_counter.add(1, {"channel": "web"})
        checkout_duration.record(elapsed_ms, {"channel": "web"})
        span.add_event("order-committed", {"elapsed_ms": round(elapsed_ms, 2)})

        logger.info("Order created in %.1f ms", elapsed_ms)
    return {"status": "created", "took_ms": round(elapsed_ms, 1)}


