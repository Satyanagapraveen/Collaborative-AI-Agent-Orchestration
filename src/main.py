import redis.asyncio as aioredis
import asyncio
import os
from uuid import UUID

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from src.db.database import engine, Base
from src.db import models
from contextlib import asynccontextmanager
from src.api.tasks import router as task_router

# Build an asynchronous client specifically for the WebSocket
async_redis = aioredis.from_url(os.getenv("REDIS_URL"))

@asynccontextmanager
async def lifespan(app:FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app=FastAPI(title="Collaborative Agent Orchestration API",lifespan=lifespan)
app.include_router(task_router)

@app.get("/health")
async def health_check():
    return {"status":"healthy","service":"api"}

@app.websocket("/ws/tasks/{task_id}")
async def websocket_task_status(websocket: WebSocket, task_id: UUID):
    await websocket.accept()
    
    pubsub = async_redis.pubsub()
    channel_name = f"task_updates:{task_id}"
    await pubsub.subscribe(channel_name)
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                status_string = message["data"].decode("utf-8")
                if status_string in ("COMPLETED", "FAILED"):
                    await websocket.send_json({
                        "task_id": str(task_id),
                        "status": status_string
                    })
                    await pubsub.unsubscribe(channel_name)
                    await websocket.close()
                    return
                
            # Pause for 100 milliseconds to prevent CPU overload
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        await pubsub.unsubscribe(channel_name)
        # --- NEW: Catch the server shutdown signal ---
    except asyncio.CancelledError:
        await pubsub.unsubscribe(channel_name)
        raise