"""User management endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)
router = APIRouter()


class User(BaseModel):
    """User model."""

    id: int
    name: str
    email: EmailStr
    is_active: bool = True


class UserCreate(BaseModel):
    """User creation model."""

    name: str
    email: EmailStr


class UserUpdate(BaseModel):
    """User update model."""

    name: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None


# Mock database
fake_users_db = [
    User(id=1, name="John Doe", email="john@example.com"),
    User(id=2, name="Jane Smith", email="jane@example.com"),
    User(id=3, name="Bob Johnson", email="bob@example.com", is_active=False),
]


@router.get("/", response_model=list[User])
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    active_only: bool = Query(True, description="Filter active users only"),
):
    """Get list of users."""
    logger.info(
        "Fetching users",
        extra={
            "event": "get_users",
            "skip": skip,
            "limit": limit,
            "active_only": active_only,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    users = fake_users_db

    if active_only:
        users = [user for user in users if user.is_active]

    result = users[skip : skip + limit]

    logger.info(
        "Users fetched successfully",
        extra={
            "event": "get_users_success",
            "count": len(result),
            "total_available": len(users),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    return result


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: int):
    """Get user by ID."""
    logger.info(
        "Fetching user",
        extra={
            "event": "get_user",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    user = next((user for user in fake_users_db if user.id == user_id), None)

    if not user:
        logger.warning(
            "User not found",
            extra={
                "event": "get_user_not_found",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(
        "User fetched successfully",
        extra={
            "event": "get_user_success",
            "user_id": user_id,
            "user_name": user.name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    return user


@router.post("/", response_model=User, status_code=201)
async def create_user(user_data: UserCreate):
    """Create a new user."""
    logger.info(
        "Creating user",
        extra={
            "event": "create_user",
            "user_name": user_data.name,
            "user_email": user_data.email,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    # Check if email already exists
    if any(user.email == user_data.email for user in fake_users_db):
        logger.warning(
            "User creation failed - email already exists",
            extra={
                "event": "create_user_email_exists",
                "user_email": user_data.email,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    new_id = max([user.id for user in fake_users_db]) + 1
    new_user = User(id=new_id, name=user_data.name, email=user_data.email)

    fake_users_db.append(new_user)

    logger.info(
        "User created successfully",
        extra={
            "event": "create_user_success",
            "user_id": new_user.id,
            "user_name": new_user.name,
            "user_email": new_user.email,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    return new_user


@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, user_data: UserUpdate):
    """Update an existing user."""
    logger.info(
        "Updating user",
        extra={
            "event": "update_user",
            "user_id": user_id,
            "update_fields": [k for k, v in user_data.model_dump(exclude_unset=True).items()],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    user_index = next(
        (i for i, user in enumerate(fake_users_db) if user.id == user_id), None
    )

    if user_index is None:
        logger.warning(
            "User update failed - user not found",
            extra={
                "event": "update_user_not_found",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )
        raise HTTPException(status_code=404, detail="User not found")

    # Update user
    user = fake_users_db[user_index]
    update_data = user_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    logger.info(
        "User updated successfully",
        extra={
            "event": "update_user_success",
            "user_id": user_id,
            "updated_fields": list(update_data.keys()),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    return user


@router.delete("/{user_id}")
async def delete_user(user_id: int):
    """Delete a user."""
    logger.info(
        "Deleting user",
        extra={
            "event": "delete_user",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    user_index = next(
        (i for i, user in enumerate(fake_users_db) if user.id == user_id), None
    )

    if user_index is None:
        logger.warning(
            "User deletion failed - user not found",
            extra={
                "event": "delete_user_not_found",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )
        raise HTTPException(status_code=404, detail="User not found")

    deleted_user = fake_users_db.pop(user_index)

    logger.info(
        "User deleted successfully",
        extra={
            "event": "delete_user_success",
            "user_id": user_id,
            "user_name": deleted_user.name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )

    return {"message": "User deleted successfully"}
