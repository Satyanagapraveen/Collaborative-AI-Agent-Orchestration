from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.agents.state import AgentState
from src.agents.nodes import research_agent, writing_agent

workflow=StateGraph(AgentState)
workflow.add_node("researcher",research_agent)
workflow.add_node("writer",writing_agent)
workflow.set_entry_point("researcher")
def check_research_status(state:AgentState):
    if state.get("status")=="FAILED":
        return END
    return "writer"

workflow.add_conditional_edges(
    "researcher",
    check_research_status
)    

workflow.add_edge("writer",END)
memory=MemorySaver()
agent_app=workflow.compile(
     checkpointer=memory
)