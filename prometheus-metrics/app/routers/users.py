"""User management API endpoints."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.database import get_session
from app.services.user_service import user_service
from app.models import User

router = APIRouter(prefix="/users", tags=["Users"])

# Pydantic models for API
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    address: Optional[str] = None
    phone: Optional[str] = None
    active: bool = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    address: Optional[str] = None
    phone: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UsersListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    size: int

@router.get("/", response_model=UsersListResponse)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_session)
):
    """Get all users with pagination."""
    users = await user_service.get_all_users(session, skip=skip, limit=limit)
    total = await user_service.get_user_count(session)
    
    return UsersListResponse(
        users=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=skip // limit + 1,
        size=len(users)
    )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get a specific user by ID."""
    user = await user_service.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    return UserResponse.model_validate(user)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new user."""
    try:
        user = await user_service.create_user(session, user_data.model_dump())
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update an existing user."""
    try:
        user = await user_service.update_user(session, user_id, user_data.model_dump(exclude_unset=True))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Delete a user (soft delete)."""
    deleted = await user_service.delete_user(session, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

@router.post("/authenticate")
async def authenticate_user(
    email: EmailStr,
    session: AsyncSession = Depends(get_session)
):
    """Authenticate a user (simplified for demo)."""
    user = await user_service.authenticate_user(session, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
    return {
        "message": "Authentication successful",
        "user": UserResponse.model_validate(user)
    }