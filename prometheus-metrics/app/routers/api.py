"""
Main API router with example endpoints for metrics demonstration.
"""

import random
import time
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.metrics_service import MetricsService

router = APIRouter()
metrics_service = MetricsService()


class UserModel(BaseModel):
    """User model for API examples."""
    id: int
    name: str
    email: str


class ResponseModel(BaseModel):
    """Generic response model."""
    success: bool
    message: str
    data: Dict[str, Any] = {}


@router.get("/users", response_model=ResponseModel)
async def get_users():
    """Get all users - example endpoint that always succeeds."""
    # Simulate some processing time
    await simulate_work(0.1, 0.3)
    
    users = [
        {"id": 1, "name": "John Doe", "email": "john@example.com"},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
    ]
    
    metrics_service.increment_counter("api_users_requested")
    
    return ResponseModel(
        success=True,
        message="Users retrieved successfully",
        data={"users": users, "count": len(users)}
    )


@router.get("/users/{user_id}", response_model=ResponseModel)
async def get_user(user_id: int):
    """Get user by ID - example endpoint with potential errors."""
    # Simulate some processing time
    await simulate_work(0.05, 0.2)
    
    # Simulate occasional errors for metrics demonstration
    if random.random() < 0.1:  # 10% chance of error
        metrics_service.increment_counter("api_errors_total", {"endpoint": "/users/{id}", "error_type": "not_found"})
        raise HTTPException(status_code=404, detail="User not found")
    
    if random.random() < 0.05:  # 5% chance of server error
        metrics_service.increment_counter("api_errors_total", {"endpoint": "/users/{id}", "error_type": "server_error"})
        raise HTTPException(status_code=500, detail="Internal server error")
    
    user = {"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"}
    
    metrics_service.increment_counter("api_user_requested", {"user_id": str(user_id)})
    
    return ResponseModel(
        success=True,
        message="User retrieved successfully",
        data={"user": user}
    )


@router.post("/users", response_model=ResponseModel)
async def create_user(user: UserModel):
    """Create a new user - example POST endpoint."""
    # Simulate some processing time for creation
    await simulate_work(0.2, 0.5)
    
    metrics_service.increment_counter("api_users_created")
    
    return ResponseModel(
        success=True,
        message="User created successfully",
        data={"user": user.dict()}
    )


@router.get("/slow-endpoint")
async def slow_endpoint():
    """Endpoint that simulates slow response for metrics demonstration."""
    # Simulate slow processing
    await simulate_work(2.0, 5.0)
    
    metrics_service.increment_counter("api_slow_requests")
    
    return {"message": "This was a slow endpoint", "processing_time": "2-5 seconds"}


@router.get("/memory-intensive")
async def memory_intensive_endpoint():
    """Endpoint that uses more memory for metrics demonstration."""
    # Create some memory usage
    large_data = [i for i in range(1000000)]  # Create a large list
    
    metrics_service.increment_counter("api_memory_intensive_requests")
    
    return {"message": "Memory intensive operation completed", "data_size": len(large_data)}


async def simulate_work(min_time: float, max_time: float):
    """Simulate work by sleeping for a random amount of time."""
    import asyncio
    sleep_time = random.uniform(min_time, max_time)
    await asyncio.sleep(sleep_time)