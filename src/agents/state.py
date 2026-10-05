from typing import Annotated, List, TypedDict, Dict, Any
import operator

class AgentState(TypedDict):
    task_id: str
    prompt: str
    status: str
    human_approved: bool
    errors: Annotated[List[str],operator.add]
    feedback: str
    agent_logs: Annotated[List[Dict[str, Any]], operator.add]