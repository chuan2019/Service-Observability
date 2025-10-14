"""User service with database operations and Prometheus metrics."""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from prometheus_client import Counter, Histogram, Gauge

from app.middleware.metrics import REGISTRY
from app.models import User
from app.database import get_session

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

USER_REGISTRATIONS = Counter(
    'user_service_registrations_total',
    'Total user registrations',
    ['source'],
    registry=REGISTRY
)

USER_AUTHENTICATIONS = Counter(
    'user_service_authentications_total',
    'Total user authentication attempts',
    ['status'],
    registry=REGISTRY
)


class UserService:
    """Service for managing users with database operations and Prometheus metrics."""

    def __init__(self):
        """Initialize the user service."""
        pass

    async def get_all_users(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        with USER_OPERATION_DURATION.labels(operation="get_all").time():
            try:
                USER_DATABASE_QUERIES.labels(query_type="select", status="started").inc()
                
                result = await session.execute(
                    select(User)
                    .where(User.active == True)
                    .offset(skip)
                    .limit(limit)
                    .order_by(User.created_at.desc())
                )
                users = result.scalars().all()
                
                USER_DATABASE_QUERIES.labels(query_type="select", status="success").inc()
                USER_OPERATIONS.labels(operation="get_all", status="success").inc()
                
                # Update active users gauge
                await self._update_active_users_count(session)
                
                return list(users)
                
            except Exception as e:
                USER_DATABASE_QUERIES.labels(query_type="select", status="error").inc()
                USER_OPERATIONS.labels(operation="get_all", status="error").inc()
                raise

    async def get_user_by_id(self, session: AsyncSession, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        with USER_OPERATION_DURATION.labels(operation="get_by_id").time():
            try:
                USER_DATABASE_QUERIES.labels(query_type="select", status="started").inc()
                
                result = await session.execute(
                    select(User).where(User.id == user_id, User.active == True)
                )
                user = result.scalar_one_or_none()
                
                USER_DATABASE_QUERIES.labels(query_type="select", status="success").inc()
                
                if user:
                    USER_OPERATIONS.labels(operation="get_by_id", status="success").inc()
                else:
                    USER_OPERATIONS.labels(operation="get_by_id", status="not_found").inc()
                
                return user
                
            except Exception as e:
                USER_DATABASE_QUERIES.labels(query_type="select", status="error").inc()
                USER_OPERATIONS.labels(operation="get_by_id", status="error").inc()
                raise

    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        """Get a user by email."""
        with USER_OPERATION_DURATION.labels(operation="get_by_email").time():
            try:
                USER_DATABASE_QUERIES.labels(query_type="select", status="started").inc()
                
                result = await session.execute(
                    select(User).where(User.email == email, User.active == True)
                )
                user = result.scalar_one_or_none()
                
                USER_DATABASE_QUERIES.labels(query_type="select", status="success").inc()
                USER_OPERATIONS.labels(operation="get_by_email", status="success").inc()
                
                return user
                
            except Exception as e:
                USER_DATABASE_QUERIES.labels(query_type="select", status="error").inc()
                USER_OPERATIONS.labels(operation="get_by_email", status="error").inc()
                raise

    async def create_user(self, session: AsyncSession, user_data: Dict[str, Any]) -> User:
        """Create a new user."""
        with USER_OPERATION_DURATION.labels(operation="create").time():
            try:
                USER_DATABASE_QUERIES.labels(query_type="insert", status="started").inc()
                
                # Create new user instance
                user = User(
                    email=user_data["email"],
                    name=user_data["name"],
                    address=user_data.get("address"),
                    phone=user_data.get("phone"),
                    active=user_data.get("active", True)
                )
                
                session.add(user)
                await session.commit()
                await session.refresh(user)
                
                USER_DATABASE_QUERIES.labels(query_type="insert", status="success").inc()
                USER_OPERATIONS.labels(operation="create", status="success").inc()
                USER_REGISTRATIONS.labels(source="api").inc()
                
                # Update active users count
                await self._update_active_users_count(session)
                
                return user
                
            except IntegrityError as e:
                await session.rollback()
                USER_DATABASE_QUERIES.labels(query_type="insert", status="error").inc()
                USER_OPERATIONS.labels(operation="create", status="duplicate_email").inc()
                raise ValueError(f"User with email {user_data['email']} already exists")
            except Exception as e:
                await session.rollback()
                USER_DATABASE_QUERIES.labels(query_type="insert", status="error").inc()
                USER_OPERATIONS.labels(operation="create", status="error").inc()
                raise

    async def update_user(self, session: AsyncSession, user_id: int, user_data: Dict[str, Any]) -> Optional[User]:
        """Update an existing user."""
        with USER_OPERATION_DURATION.labels(operation="update").time():
            try:
                # First get the user
                user = await self.get_user_by_id(session, user_id)
                if not user:
                    USER_OPERATIONS.labels(operation="update", status="not_found").inc()
                    return None
                
                USER_DATABASE_QUERIES.labels(query_type="update", status="started").inc()
                
                # Update fields if provided
                if "name" in user_data and user_data["name"]:
                    user.name = user_data["name"]
                if "email" in user_data and user_data["email"]:
                    user.email = user_data["email"]
                if "address" in user_data:
                    user.address = user_data["address"]
                if "phone" in user_data:
                    user.phone = user_data["phone"]
                if "active" in user_data:
                    user.active = user_data["active"]
                
                user.updated_at = datetime.utcnow()
                
                await session.commit()
                await session.refresh(user)
                
                USER_DATABASE_QUERIES.labels(query_type="update", status="success").inc()
                USER_OPERATIONS.labels(operation="update", status="success").inc()
                
                return user
                
            except IntegrityError as e:
                await session.rollback()
                USER_DATABASE_QUERIES.labels(query_type="update", status="error").inc()
                USER_OPERATIONS.labels(operation="update", status="duplicate_email").inc()
                raise ValueError(f"Email {user_data.get('email')} is already taken")
            except Exception as e:
                await session.rollback()
                USER_DATABASE_QUERIES.labels(query_type="update", status="error").inc()
                USER_OPERATIONS.labels(operation="update", status="error").inc()
                raise

    async def delete_user(self, session: AsyncSession, user_id: int) -> bool:
        """Soft delete a user (mark as inactive)."""
        with USER_OPERATION_DURATION.labels(operation="delete").time():
            try:
                # Get the user first
                user = await self.get_user_by_id(session, user_id)
                if not user:
                    USER_OPERATIONS.labels(operation="delete", status="not_found").inc()
                    return False
                
                USER_DATABASE_QUERIES.labels(query_type="update", status="started").inc()
                
                # Soft delete by marking as inactive
                user.active = False
                user.updated_at = datetime.utcnow()
                
                await session.commit()
                
                USER_DATABASE_QUERIES.labels(query_type="update", status="success").inc()
                USER_OPERATIONS.labels(operation="delete", status="success").inc()
                
                # Update active users count
                await self._update_active_users_count(session)
                
                return True
                
            except Exception as e:
                await session.rollback()
                USER_DATABASE_QUERIES.labels(query_type="update", status="error").inc()
                USER_OPERATIONS.labels(operation="delete", status="error").inc()
                raise

    async def authenticate_user(self, session: AsyncSession, email: str, password: str = None) -> Optional[User]:
        """Authenticate a user (simplified for demo - no real password checking)."""
        with USER_OPERATION_DURATION.labels(operation="authenticate").time():
            try:
                user = await self.get_user_by_email(session, email)
                
                # For demo purposes, we'll just check if user exists and is active
                if user and user.active:
                    USER_AUTHENTICATIONS.labels(status="success").inc()
                    USER_OPERATIONS.labels(operation="authenticate", status="success").inc()
                    return user
                else:
                    USER_AUTHENTICATIONS.labels(status="failed").inc()
                    USER_OPERATIONS.labels(operation="authenticate", status="failed").inc()
                    return None
                    
            except Exception as e:
                USER_AUTHENTICATIONS.labels(status="error").inc()
                USER_OPERATIONS.labels(operation="authenticate", status="error").inc()
                raise

    async def get_user_count(self, session: AsyncSession) -> int:
        """Get total count of active users."""
        with USER_OPERATION_DURATION.labels(operation="count").time():
            try:
                USER_DATABASE_QUERIES.labels(query_type="count", status="started").inc()
                
                result = await session.execute(
                    select(User.id).where(User.active == True)
                )
                count = len(result.scalars().all())
                
                USER_DATABASE_QUERIES.labels(query_type="count", status="success").inc()
                USER_OPERATIONS.labels(operation="count", status="success").inc()
                
                return count
                
            except Exception as e:
                USER_DATABASE_QUERIES.labels(query_type="count", status="error").inc()
                USER_OPERATIONS.labels(operation="count", status="error").inc()
                raise

    async def _update_active_users_count(self, session: AsyncSession) -> None:
        """Update the active users gauge metric."""
        try:
            count = await self.get_user_count(session)
            ACTIVE_USERS.set(count)
        except Exception:
            # Don't fail the main operation if metrics update fails
            pass

# Global service instance
user_service = UserService()