from fastapi import FastAPI

app=FastAPI(title="Collaborative Agent Orchestration API")
@app.get("/health")
async def health_check():
    return {"status":"healthy","service":"api"}