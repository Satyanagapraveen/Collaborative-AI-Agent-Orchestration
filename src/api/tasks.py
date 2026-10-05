import os
import redis
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from src.db.database import get_db
from src.db.models import Task
from src.api.schemas import TaskRequest, TaskResponse
from src.worker.tasks import run_agent_workflow

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])

@router.post("",response_model=TaskResponse, status_code=202)
async def create_task(request:TaskRequest, db:AsyncSession=Depends(get_db)):
    new_task=Task(prompt=request.prompt, status="PENDING")
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    # TODO: In Phase 3, we will trigger the Celery worker here
     # Dispatch to Celery
    run_agent_workflow.delay(str(new_task.id), request.prompt)
    
    return new_task

@router.get("/{task_id}",response_model=TaskResponse)
async def get_task(task_id: UUID, db:AsyncSession=Depends(get_db)):
    result= await db.execute(select(Task).where(Task.id==task_id))
    task=result.scalars().first()
    if not task:
        return HTTPException(status_code=404, detail="Task not found")
    return task

redis_client = redis.from_url(os.getenv("REDIS_URL"))

@router.post("/{task_id}/approve")
async def approve_task(task_id: UUID, db: AsyncSession = Depends(get_db)):
    # 1. Verify the task exists and is waiting for approval
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    if task.status != "AWAITING_APPROVAL":
        raise HTTPException(
            status_code=400, 
            detail=f"Task is in status {task.status}, not AWAITING_APPROVAL"
        )
        
    # 2. Retrieve the final draft from the Redis scratchpad
    redis_key = f"task:{str(task_id)}:workspace"
    workspace_data_raw = redis_client.get(redis_key)
    
    if workspace_data_raw:
        workspace_data = json.loads(workspace_data_raw)
        draft = workspace_data.get("draft", "No draft found in scratchpad.")
        
        # --- NEW EXTRACTION LOGIC ---
        if isinstance(draft, list):
            # Extract the 'text' value from each dictionary in the list and join them
            extracted_text = "".join([
                item.get("text", "") for item in draft if isinstance(item, dict)
            ])
            draft = extracted_text
        elif not isinstance(draft, str):
            # Fallback: force any other weird data types into a string
            draft = str(draft)
        # ----------------------------
        
        # Now it is guaranteed to be a flat string, safe for PostgreSQL VARCHAR
        task.result = draft
    else:
        # Fallback if Redis data expired or went missing
        task.result = "Error: Workspace data expired or not found."