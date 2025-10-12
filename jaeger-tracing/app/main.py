"""Main FastAPI application with Jaeger tracing."""

from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

import json

from app.services import OrderService, PaymentService, UserService
from config import get_tracer, instrument_fastapi, setup_tracing


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Starting FastAPI application with Jaeger tracing...")
    setup_tracing()
    yield
    # Shutdown
    print("Shutting down FastAPI application...")


# Create FastAPI app
app = FastAPI(
    title="FastAPI Jaeger Tracing Demo",
    description="A demo application showcasing distributed tracing with Jaeger",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument FastAPI with OpenTelemetry
instrument_fastapi(app)

# Get tracer for custom spans
tracer = get_tracer(__name__)

# Initialize services
user_service = UserService()
order_service = OrderService()
payment_service = PaymentService()


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    with tracer.start_as_current_span("root_endpoint") as span:
        span.set_attribute("endpoint", "/")
        span.set_attribute("method", "GET")
        return {"message": "FastAPI with Jaeger Tracing Demo", "status": "running"}


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    with tracer.start_as_current_span("health_check") as span:
        span.set_attribute("endpoint", "/health")
        span.set_attribute("method", "GET")
        return {"status": "healthy", "service": "fastapi-jaeger-demo"}


@app.get("/users/{user_id}")
async def get_user(user_id: int) -> Dict[str, Any]:
    """Get user by ID."""
    with tracer.start_as_current_span("get_user_endpoint") as span:
        span.set_attribute("endpoint", "/users/{user_id}")
        span.set_attribute("user_id", user_id)
        span.set_attribute("method", "GET")

        try:
            user = await user_service.get_user(user_id)
            span.set_attribute("user.found", True)
            return user
        except ValueError as e:
            span.set_attribute("user.found", False)
            span.set_attribute("error", str(e))
            raise HTTPException(status_code=404, detail=str(e))


@app.post("/users")
async def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new user."""
    with tracer.start_as_current_span("create_user_endpoint") as span:
        span.set_attribute("endpoint", "/users")
        span.set_attribute("method", "POST")
        span.set_attribute("user.name", user_data.get("name", ""))

        user = await user_service.create_user(user_data)
        span.set_attribute("user.created_id", user["id"])
        return user


@app.get("/orders/{order_id}")
async def get_order(order_id: int) -> Dict[str, Any]:
    """Get order by ID."""
    with tracer.start_as_current_span("get_order_endpoint") as span:
        span.set_attribute("endpoint", "/orders/{order_id}")
        span.set_attribute("order_id", order_id)
        span.set_attribute("method", "GET")

        try:
            order = await order_service.get_order(order_id)
            span.set_attribute("order.found", True)
            return order
        except ValueError as e:
            span.set_attribute("order.found", False)
            span.set_attribute("error", str(e))
            raise HTTPException(status_code=404, detail=str(e))


@app.post("/orders")
async def create_order(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new order."""
    with tracer.start_as_current_span("create_order_endpoint") as span:
        span.set_attribute("endpoint", "/orders")
        span.set_attribute("method", "POST")
        span.set_attribute("order.user_id", order_data.get("user_id", 0))
        span.set_attribute("order.amount", order_data.get("amount", 0.0))

        # This will create a distributed trace across multiple services
        order = await order_service.create_order(order_data)
        span.set_attribute("order.created_id", order["id"])
        return order


@app.post("/payments")
async def process_payment(payment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a payment."""
    with tracer.start_as_current_span("process_payment_endpoint") as span:
        span.set_attribute("endpoint", "/payments")
        span.set_attribute("method", "POST")
        span.set_attribute("payment.order_id", payment_data.get("order_id", 0))
        span.set_attribute("payment.amount", payment_data.get("amount", 0.0))

        payment = await payment_service.process_payment(payment_data)
        span.set_attribute("payment.status", payment["status"])
        return payment


@app.get("/demo/full-flow/{user_id}")
async def demo_full_flow(user_id: int) -> Dict[str, Any]:
    """Demonstrate a full flow with multiple service calls."""
    with tracer.start_as_current_span("demo_full_flow") as span:
        span.set_attribute("endpoint", "/demo/full-flow/{user_id}")
        span.set_attribute("user_id", user_id)
        span.set_attribute("method", "GET")

        try:
            # Get user
            user = await user_service.get_user(user_id)
            span.set_attribute("step", "user_retrieved")

            # Create order
            order_data = {
                "user_id": user_id,
                "amount": 99.99,
                "items": ["item1", "item2"],
            }
            order = await order_service.create_order(order_data)
            span.set_attribute("step", "order_created")
            span.set_attribute("order.id", order["id"])

            # Process payment
            payment_data = {
                "order_id": order["id"],
                "amount": order["amount"],
                "method": "credit_card",
            }
            payment = await payment_service.process_payment(payment_data)
            span.set_attribute("step", "payment_processed")
            span.set_attribute("payment.status", payment["status"])

            return {
                "user": user,
                "order": order,
                "payment": payment,
                "flow_status": "completed",
            }
        except Exception as e:
            span.set_attribute("error", str(e))
            span.set_attribute("flow_status", "failed")
            raise HTTPException(status_code=500, detail=f"Flow failed: {str(e)}")

@app.get("/api-spec", include_in_schema=False)
def openapi_pretty():
    openapi_spec = app.openapi()
    pretty_json = json.dumps(openapi_spec, indent=4, ensure_ascii=False)
    return Response(content=pretty_json, media_type="application/json")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
