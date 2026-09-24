import os
import asyncio
from celery import Celery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.worker.celery_app import celery_app
from src.db.models import Task
from sqlalchemy import select
from src.agents.graph import agent_app

@celery_app.task(name="run_agent_workflow")
def run_agent_workflow(task_id: str, prompt: str):
    async def _execute_workflow():
        
        # 1. Build a brand new, isolated engine specifically for this one task run
        engine = create_async_engine(os.getenv("DATABASE_URL"))
        IsolatedSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

        # 2. Use the isolated session
        async with IsolatedSessionLocal() as session:
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
                final_state = await agent_app.ainvoke(
                    initial_state,
                    config={"configurable": {"thread_id": task_id}}
                )
                
                task.status = final_state.get("status", "FAILED")
                if task.status == "FAILED":
                    task.result = f"Errors: {', '.join(final_state.get('errors', []))}"
                
                await session.commit()
                
            except Exception as e:
                task.status = "FAILED"
                task.result = f"Fatal Orchestration Error: {str(e)}"
                await session.commit()
                
            finally:
                # 3. Cleanly dispose of the isolated engine when finished
                await engine.dispose()

    asyncio.run(_execute_workflow())