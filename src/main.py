from fastapi import FastAPI
from src.db.database import engine, Base
from src.db import models
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app:FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app=FastAPI(title="Collaborative Agent Orchestration API",lifespan=lifespan)
@app.get("/health")
async def health_check():
    return {"status":"healthy","service":"api"}