"""User service with Prometheus metrics."""

import asyncio
import random
from typing import Any, Dict, List

from prometheus_client import Counter, Histogram, Gauge
from app.middleware.metrics import REGISTRY

# User service specific metrics
USER_OPERATIONS = Counter(
    'user_service_operations_total',
    'Total user service operations',
    ['operation', 'status'],
    registry=REGISTRY
)

USER_OPERATION_DURATION = Histogram(
    'user_service_operation_duration_seconds',
    'User service operation duration',
    ['operation'],
    registry=REGISTRY
)

ACTIVE_USERS = Gauge(
    'user_service_active_users',
    'Number of active users',
    registry=REGISTRY
)

USER_DATABASE_QUERIES = Counter(
    'user_service_db_queries_total',
    'Total database queries in user service',
    ['query_type', 'status'],
    registry=REGISTRY
)


class UserService:
    """Service for managing users with Prometheus metrics."""

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
        # Update active users gauge
        self._update_active_users_count()

    def _update_active_users_count(self):
        """Update the active users gauge."""
        active_count = sum(1 for user in self.users.values() if user.get("status") == "active")
        ACTIVE_USERS.set(active_count)

    async def get_user(self, user_id: int) -> Dict[str, Any]:
        """Get user by ID with metrics."""
        with USER_OPERATION_DURATION.labels(operation="get_user").time():
            try:
                # Record database query
                USER_DATABASE_QUERIES.labels(query_type="select", status="attempted").inc()
                
                # Simulate database lookup delay
                await asyncio.sleep(random.uniform(0.01, 0.05))

                if user_id not in self.users:
                    USER_DATABASE_QUERIES.labels(query_type="select", status="not_found").inc()
                    USER_OPERATIONS.labels(operation="get_user", status="not_found").inc()
                    raise ValueError(f"User {user_id} not found")

                user = self.users[user_id].copy()
                
                # Add some dynamic fields for demo
                user["last_login"] = "2024-01-15T10:30:00Z"
                user["login_count"] = random.randint(5, 100)

                USER_DATABASE_QUERIES.labels(query_type="select", status="success").inc()
                USER_OPERATIONS.labels(operation="get_user", status="success").inc()
                
                return user

            except Exception as e:
                USER_OPERATIONS.labels(operation="get_user", status="error").inc()
                raise e

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user with metrics."""
        with USER_OPERATION_DURATION.labels(operation="create_user").time():
            try:
                # Record database query
                USER_DATABASE_QUERIES.labels(query_type="insert", status="attempted").inc()
                
                # Validate required fields
                if not user_data.get("name") or not user_data.get("email"):
                    USER_OPERATIONS.labels(operation="create_user", status="validation_error").inc()
                    raise ValueError("Name and email are required")

                # Simulate user creation delay
                await asyncio.sleep(random.uniform(0.02, 0.08))

                # Create new user
                user_id = self.next_id
                self.next_id += 1

                user = {
                    "id": user_id,
                    "name": user_data["name"],
                    "email": user_data["email"],
                    "status": user_data.get("status", "active"),
                    "created_at": "2024-01-15T10:30:00Z",
                    "login_count": 0,
                }

                self.users[user_id] = user
                self._update_active_users_count()

                USER_DATABASE_QUERIES.labels(query_type="insert", status="success").inc()
                USER_OPERATIONS.labels(operation="create_user", status="success").inc()

                return user.copy()

            except Exception as e:
                USER_OPERATIONS.labels(operation="create_user", status="error").inc()
                raise e

    async def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user with metrics."""
        with USER_OPERATION_DURATION.labels(operation="update_user").time():
            try:
                USER_DATABASE_QUERIES.labels(query_type="update", status="attempted").inc()
                
                # Simulate database update delay
                await asyncio.sleep(random.uniform(0.02, 0.06))

                if user_id not in self.users:
                    USER_DATABASE_QUERIES.labels(query_type="update", status="not_found").inc()
                    USER_OPERATIONS.labels(operation="update_user", status="not_found").inc()
                    raise ValueError(f"User {user_id} not found")

                # Update user data
                user = self.users[user_id]
                for key, value in user_data.items():
                    if key != "id":  # Don't allow ID changes
                        user[key] = value

                user["updated_at"] = "2024-01-15T10:30:00Z"
                self._update_active_users_count()

                USER_DATABASE_QUERIES.labels(query_type="update", status="success").inc()
                USER_OPERATIONS.labels(operation="update_user", status="success").inc()

                return user.copy()

            except Exception as e:
                USER_OPERATIONS.labels(operation="update_user", status="error").inc()
                raise e

    async def delete_user(self, user_id: int) -> Dict[str, str]:
        """Delete user with metrics."""
        with USER_OPERATION_DURATION.labels(operation="delete_user").time():
            try:
                USER_DATABASE_QUERIES.labels(query_type="delete", status="attempted").inc()
                
                # Simulate database delete delay
                await asyncio.sleep(random.uniform(0.01, 0.04))

                if user_id not in self.users:
                    USER_DATABASE_QUERIES.labels(query_type="delete", status="not_found").inc()
                    USER_OPERATIONS.labels(operation="delete_user", status="not_found").inc()
                    raise ValueError(f"User {user_id} not found")

                del self.users[user_id]
                self._update_active_users_count()

                USER_DATABASE_QUERIES.labels(query_type="delete", status="success").inc()
                USER_OPERATIONS.labels(operation="delete_user", status="success").inc()

                return {"message": f"User {user_id} deleted successfully"}

            except Exception as e:
                USER_OPERATIONS.labels(operation="delete_user", status="error").inc()
                raise e

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users with metrics."""
        with USER_OPERATION_DURATION.labels(operation="get_all_users").time():
            try:
                USER_DATABASE_QUERIES.labels(query_type="select_all", status="attempted").inc()
                
                # Simulate database query delay
                await asyncio.sleep(random.uniform(0.05, 0.15))

                users = [user.copy() for user in self.users.values()]
                
                USER_DATABASE_QUERIES.labels(query_type="select_all", status="success").inc()
                USER_OPERATIONS.labels(operation="get_all_users", status="success").inc()

                return users

            except Exception as e:
                USER_OPERATIONS.labels(operation="get_all_users", status="error").inc()
                raise e

    async def validate_user_exists(self, user_id: int) -> bool:
        """Validate if user exists - used by other services."""
        with USER_OPERATION_DURATION.labels(operation="validate_user").time():
            try:
                USER_DATABASE_QUERIES.labels(query_type="exists", status="attempted").inc()
                
                # Simulate validation delay
                await asyncio.sleep(random.uniform(0.005, 0.02))

                exists = user_id in self.users
                
                USER_DATABASE_QUERIES.labels(query_type="exists", status="success").inc()
                USER_OPERATIONS.labels(operation="validate_user", status="success").inc()

                return exists

            except Exception as e:
                USER_OPERATIONS.labels(operation="validate_user", status="error").inc()
                raise e