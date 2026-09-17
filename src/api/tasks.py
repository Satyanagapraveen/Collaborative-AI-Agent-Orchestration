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