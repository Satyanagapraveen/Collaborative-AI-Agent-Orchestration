import asyncio
from src.worker.celery_app import celery_app
from src.db.database import AsyncSessionLocal
from src.db.models import Task
from sqlalchemy import select
from src.agents.graph import agent_app

@celery_app.task(name="run_agent_workflow")
def run_agent_workflow(task_id: str, prompt: str):
    async def _execute_workflow():
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalars().first()
            
            if not task:
                return
            
            task.status = "RUNNING"
            await session.commit()
            
            initial_state = {
                "task_id": task_id,
                "prompt": prompt,
                "status": "RUNNING",
                "human_approved": False,
                "errors": []
            }
            
            try:
                final_state = await agent_app.ainvoke(initial_state)
                
                task.status = final_state.get("status", "FAILED")
                if task.status == "FAILED":
                    task.result = f"Errors: {', '.join(final_state.get('errors', []))}"
                
                await session.commit()
                
            except Exception as e:
                task.status = "FAILED"
                task.result = f"Fatal Orchestration Error: {str(e)}"
                await session.commit()

    asyncio.run(_execute_workflow())