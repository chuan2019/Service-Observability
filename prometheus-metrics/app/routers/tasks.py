"""
Task management router for background task examples.
"""

import asyncio
import random
from typing import Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from app.services.metrics_service import MetricsService

router = APIRouter()
metrics_service = MetricsService()

# In-memory task storage (use a database in production)
tasks: Dict[str, Dict] = {}


class TaskModel(BaseModel):
    """Task model."""
    id: str
    name: str
    status: str
    progress: int = 0
    result: Optional[str] = None


class TaskRequest(BaseModel):
    """Task creation request."""
    name: str
    duration: int = 10  # seconds


@router.post("/", response_model=TaskModel)
async def create_task(task_request: TaskRequest, background_tasks: BackgroundTasks):
    """Create a new background task."""
    task_id = f"task_{random.randint(1000, 9999)}"
    
    task = {
        "id": task_id,
        "name": task_request.name,
        "status": "pending",
        "progress": 0,
        "result": None
    }
    
    tasks[task_id] = task
    
    # Add background task
    background_tasks.add_task(process_task, task_id, task_request.duration)
    
    metrics_service.increment_counter("tasks_created")
    
    return TaskModel(**task)


@router.get("/", response_model=List[TaskModel])
async def list_tasks():
    """List all tasks."""
    return [TaskModel(**task) for task in tasks.values()]


@router.get("/{task_id}", response_model=TaskModel)
async def get_task(task_id: str):
    """Get task by ID."""
    if task_id not in tasks:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskModel(**tasks[task_id])


async def process_task(task_id: str, duration: int):
    """Process a task in the background."""
    task = tasks[task_id]
    task["status"] = "running"
    
    try:
        # Simulate task processing with progress updates
        for i in range(duration):
            await asyncio.sleep(1)  # Sleep for 1 second
            task["progress"] = int((i + 1) / duration * 100)
            
            # Simulate occasional task failures
            if random.random() < 0.1:  # 10% chance of failure
                task["status"] = "failed"
                task["result"] = "Task failed due to random error"
                metrics_service.increment_counter("tasks_failed")
                return
        
        task["status"] = "completed"
        task["progress"] = 100
        task["result"] = f"Task {task_id} completed successfully"
        metrics_service.increment_counter("tasks_completed")
        
    except Exception as e:
        task["status"] = "failed"
        task["result"] = f"Task failed: {str(e)}"
        metrics_service.increment_counter("tasks_failed")