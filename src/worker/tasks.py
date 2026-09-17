import asyncio
from src.worker.celery_app import celery_app
from src.db.database import AsyncSessionLocal
from src.db.models import Task
from sqlalchemy import select

@celery_app.task(name="run_agent_workflow")
def run_agent_workflow(task_id:str, prompt:str):
    async def _execute_workflow():
        async with AsyncSessionLocal() as session:
            result= await session.execute(select(Task).where(Task.id==task_id))
            task=result.scalars().first()
            if not task:
                return 

            task.status="RUNNING"
            await session.commit()

            await asyncio.sleep(10)

            task.status="COMPLETED"
            task.result=f"simulated result for:{prompt}"
            await session.commit()
    asyncio.run(_execute_workflow())
        
