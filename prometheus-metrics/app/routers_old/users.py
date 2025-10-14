"""User management API routes with Prometheus metrics."""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.services.user_service import UserService

router = APIRouter()
user_service = UserService()


class UserCreateModel(BaseModel):
    """Model for creating a new user."""
    name: str
    email: EmailStr
    status: str = "active"


class UserUpdateModel(BaseModel):
    """Model for updating a user."""
    name: str = None
    email: EmailStr = None
    status: str = None


class UserResponseModel(BaseModel):
    """Model for user response."""
    id: int
    name: str
    email: str
    status: str
    created_at: str = None
    updated_at: str = None
    last_login: str = None
    login_count: int = None


@router.get("/", response_model=List[UserResponseModel])
async def get_all_users():
    """Get all users."""
    try:
        users = await user_service.get_all_users()
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserResponseModel)
async def get_user(user_id: int):
    """Get user by ID."""
    try:
        user = await user_service.get_user(user_id)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}"
        )


@router.post("/", response_model=UserResponseModel, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreateModel):
    """Create a new user."""
    try:
        user = await user_service.create_user(user_data.dict())
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponseModel)
async def update_user(user_id: int, user_data: UserUpdateModel):
    """Update user by ID."""
    try:
        # Filter out None values
        update_data = {k: v for k, v in user_data.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update"
            )
        
        user = await user_service.update_user(user_id, update_data)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/{user_id}")
async def delete_user(user_id: int):
    """Delete user by ID."""
    try:
        result = await user_service.delete_user(user_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.get("/{user_id}/validate")
async def validate_user_exists(user_id: int):
    """Validate if user exists - utility endpoint for other services."""
    try:
        exists = await user_service.validate_user_exists(user_id)
        return {"user_id": user_id, "exists": exists}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate user: {str(e)}"
        )