import os
import asyncio
import json
import redis
from celery import Celery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.worker.celery_app import celery_app
from src.db.models import Task
from sqlalchemy import select
from src.agents.graph import agent_app
from src.worker.celery_app import celery_app

redis_client = redis.from_url(os.getenv("REDIS_URL"))

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
            # --- NEW: Add a delay to let the WebSocket connect ---
            await asyncio.sleep(1.5)
            
            task.status = "RUNNING"
            await session.commit()
             # --- NEW: Broadcast the RUNNING status to the WebSocket ---
            redis_client.publish(f"task_updates:{task_id}", "RUNNING")
            
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
                # --- NEW: Broadcast the paused/failed status to the WebSocket ---
                redis_client.publish(f"task_updates:{task_id}", task.status)
                
            except Exception as e:
                task.status = "FAILED"
                task.result = f"Fatal Orchestration Error: {str(e)}"
                await session.commit()
                # --- NEW: Broadcast the fatal error status ---
                redis_client.publish(f"task_updates:{task_id}", "FAILED")
                
            finally:
                # 3. Cleanly dispose of the isolated engine when finished
                await engine.dispose()

    asyncio.run(_execute_workflow())

@celery_app.task(name="resume_agent_workflow")
def resume_agent_workflow(task_id: str, approved: bool, feedback: str):
    async def _execute_resume():
        engine = create_async_engine(os.getenv("DATABASE_URL"))
        IsolatedSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

        async with IsolatedSessionLocal() as session:
            result = await session.execute(select(Task).where(Task.id == task_id))
            task = result.scalars().first()
            if not task:
                return
            # --- NEW: Broadcast that the system is processing the approval ---
            redis_client.publish(f"task_updates:{task_id}", "RESUMED")


            # 1. Update the LangGraph state with the human's feedback
            config = {"configurable": {"thread_id": task_id}}
            agent_app.update_state(
                config,
                {"human_approved": approved, "feedback": feedback}
            )

            # 2. Resume the graph (it will now run the publisher node)
            final_state = await agent_app.ainvoke(None, config)

            # 3. Extract the clean string from Redis and save to Postgres
            redis_key = f"task:{task_id}:workspace"
            workspace_data_raw = redis_client.get(redis_key)
            if workspace_data_raw:
                workspace_data = json.loads(workspace_data_raw)
                draft = workspace_data.get("draft", "")
                
                if isinstance(draft, list):
                    draft = "".join([item.get("text", "") for item in draft if isinstance(item, dict)])
                elif not isinstance(draft, str):
                    draft = str(draft)
                    
                task.result = draft
            else:
                task.result = "Error: Workspace data expired."

            task.status = final_state.get("status", "COMPLETED")
             # --- NEW: Broadcast the final completion status ---
            redis_client.publish(f"task_updates:{task_id}", task.status)
            await session.commit()
            await engine.dispose()

    asyncio.run(_execute_resume())