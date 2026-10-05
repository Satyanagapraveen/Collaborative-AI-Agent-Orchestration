from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class AgentLogScheam(BaseModel):
    agent: str
    action: str
    timestamp: datetime
class TaskRequest(BaseModel):
    prompt: str

class TaskResponse(BaseModel):
    id: UUID
    prompt: str
    status: str
    result: Optional[str]=None
    agent_logs: Optional[List[AgentLogScheam]]=None
    created_at: datetime
    updated_at: datetime

    model_config= ConfigDict(from_attributes=True)

class ApprovalRequest(BaseModel):
    approved: bool
    feedback: str

class ApprovalResponse(BaseModel):
    task_id: UUID
    status: str