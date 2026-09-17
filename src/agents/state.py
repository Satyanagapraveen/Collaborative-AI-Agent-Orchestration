from typing import Annotated, List, TypedDict
import operator

class AgentState(TypedDict):
    task_id: str
    prompt: str
    status: str
    human_approved: bool
    errors: Annotated[List[str],operator.add]