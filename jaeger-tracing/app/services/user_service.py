"""User service with distributed tracing."""

import asyncio
import random
from typing import Any, Dict, List

from config import get_tracer

tracer = get_tracer(__name__)


class UserService:
    """Service for managing users with tracing."""

    def __init__(self):
        self.users: Dict[int, Dict[str, Any]] = {
            1: {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "status": "active",
            },
            2: {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane@example.com",
                "status": "active",
            },
            3: {
                "id": 3,
                "name": "Bob Johnson",
                "email": "bob@example.com",
                "status": "inactive",
            },
        }
        self.next_id = 4

    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID with tracing."""
        with tracer.start_as_current_span("user_service.get_user") as span:
            span.set_attribute("service", "user")
            span.set_attribute("operation", "get_user")
            span.set_attribute("user_id", user_id)

            # Simulate database lookup delay
            await asyncio.sleep(random.uniform(0.01, 0.05))

            if user_id not in self.users:
                span.set_attribute("user.found", False)
                span.set_attribute("error.type", "not_found")
                raise ValueError(f"User {user_id} not found")

            user = self.users[user_id]
            span.set_attribute("user.found", True)
            span.set_attribute("user.name", user["name"])
            span.set_attribute("user.status", user["status"])

            return user

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user with tracing."""
        with tracer.start_as_current_span("user_service.create_user") as span:
            span.set_attribute("service", "user")
            span.set_attribute("operation", "create_user")
            span.set_attribute("user.name", user_data.get("name", ""))
            span.set_attribute("user.email", user_data.get("email", ""))

            # Simulate user validation
            await self._validate_user_data(user_data)

            # Simulate database save delay
            await asyncio.sleep(random.uniform(0.02, 0.08))

            user = {
                "id": self.next_id,
                "name": user_data["name"],
                "email": user_data["email"],
                "status": "active",
            }

            self.users[self.next_id] = user
            span.set_attribute("user.created_id", self.next_id)
            self.next_id += 1

            return user

    async def _validate_user_data(self, user_data: Dict[str, Any]) -> None:
        """Validate user data with tracing."""
        with tracer.start_as_current_span("user_service.validate_user_data") as span:
            span.set_attribute("service", "user")
            span.set_attribute("operation", "validate_user_data")

            # Simulate validation delay
            await asyncio.sleep(random.uniform(0.005, 0.02))

            required_fields = ["name", "email"]
            missing_fields = [
                field for field in required_fields if field not in user_data
            ]

            if missing_fields:
                span.set_attribute("validation.success", False)
                span.set_attribute("validation.missing_fields", str(missing_fields))
                raise ValueError(f"Missing required fields: {missing_fields}")

            span.set_attribute("validation.success", True)

    async def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        """Get orders for a user with tracing."""
        with tracer.start_as_current_span("user_service.get_user_orders") as span:
            span.set_attribute("service", "user")
            span.set_attribute("operation", "get_user_orders")
            span.set_attribute("user_id", user_id)

            # Simulate database query delay
            await asyncio.sleep(random.uniform(0.01, 0.04))

            # Mock orders for demonstration
            orders = [
                {"id": 101, "user_id": user_id, "amount": 29.99, "status": "completed"},
                {"id": 102, "user_id": user_id, "amount": 49.99, "status": "pending"},
            ]

            span.set_attribute("orders.count", len(orders))
            return orders
