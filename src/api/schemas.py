from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class TaskRequest(BaseModel):
    prompt: str

class TaskResponse(BaseModel):
    id: UUID
    prompt: str
    status: str
    result: Optional[str]=None
    agent_logs: Optional[List[dict[str,Any]]]=None
    created_at: datetime
    updated_at: datetime

    model_config= ConfigDict(from_attributes=True)