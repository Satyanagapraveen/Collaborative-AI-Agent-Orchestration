from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from src.agents.state import AgentState
from src.agents.nodes import research_agent, writing_agent, publisher_agent # Import the new node

workflow = StateGraph(AgentState)

workflow.add_node("researcher", research_agent)
workflow.add_node("writer", writing_agent)
workflow.add_node("publisher", publisher_agent) # Add the node

workflow.set_entry_point("researcher")

def check_research_status(state: AgentState):
    if state.get("status") == "FAILED":
        return END
    return "writer"

workflow.add_conditional_edges(
    "researcher", 
    check_research_status,
    {
        "writer": "writer",
        END: END
    }
)
workflow.add_edge("writer", "publisher") # Route writer to publisher
workflow.add_edge("publisher", END)

memory = MemorySaver()

# We pause the graph right BEFORE the publisher runs
agent_app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["publisher"] 
)