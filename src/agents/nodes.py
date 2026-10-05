import logging
import os
from datetime import datetime, timezone
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.state import AgentState
from src.agents.scratchpad import write_to_scratchpad, read_from_scratchpad
from src.agents.tools import simulated_search_tool
from src.logs.logger import log_agent_action

def research_agent(state:AgentState)->dict:
    task_id=state["task_id"]
    prompt=state["prompt"]
    log_agent_action(task_id,"ResearchAgent",f"start researching for: {prompt}")
    max_retries=2
    research_data=""
    for attempt in range(max_retries):
        try:
            research_data = simulated_search_tool(prompt)
            log_agent_action(task_id, "ResearchAgent", "Tool execution successful.")
            break 
        except Exception as e:
            log_agent_action(task_id, "ResearchAgent", f"Tool failed on attempt {attempt+1}: {str(e)}", logging.ERROR)
            if attempt == max_retries - 1:
                return {"errors": [f"Research failed: {str(e)}"], "status": "FAILED"}
                
    write_to_scratchpad(task_id, {"research_data": research_data})
    log_agent_action(task_id, "ResearchAgent", "Research saved to scratchpad.")
    
    return {"agent_logs": [{"agent": "ResearchAgent", "action": f"Searching for {prompt}", "timestamp": datetime.now(timezone.utc).isoformat()}]}
def writing_agent(state: AgentState) -> dict:
    task_id = state["task_id"]
    log_agent_action(task_id, "WritingAgent", "Starting draft generation.")
    
    workspace_data = read_from_scratchpad(task_id)
    research_data = workspace_data.get("research_data", "")
    
    llm = ChatGoogleGenerativeAI(model=os.getenv("LLM_MODEL"), temperature=0, api_key=os.getenv("LLM_API_KEY"))
    
    messages = [
        SystemMessage(content="You are a senior technical writer. Summarize the provided research concisely."),
        HumanMessage(content=f"Research Data: {research_data}\n\nUser Request: {state['prompt']}")
    ]
    
    response = llm.invoke(messages)
    
    workspace_data["draft"] = response.content
    write_to_scratchpad(task_id, workspace_data)
    
    log_agent_action(task_id, "WritingAgent", "Draft generated and saved to scratchpad.")
    
    return {"status": "AWAITING_APPROVAL", "agent_logs": [{"agent": "WritingAgent", "action": "Drafting comparison summary", "timestamp": datetime.now(timezone.utc).isoformat()}]}


def publisher_agent(state: AgentState) -> dict:
    task_id = state["task_id"]
    log_agent_action(task_id, "PublisherAgent", "Human approval received. Publishing final result.")
    
    # In a real system, this would send an email or push to a live database.
    # We just update the state to signal it is completely finished.
    return {"status": "COMPLETED", "agent_logs": [{"agent": "PublisherAgent", "action": "Publishing final result", "timestamp": datetime.now(timezone.utc).isoformat()}]}