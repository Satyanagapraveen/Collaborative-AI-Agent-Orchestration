flaky_tool_attempts={}

def simulated_search_tool(query:str) ->str:
    if query=="__FLAKY_TEST__":
        attempts=flaky_tool_attempts.get(query,0)
        if attempts==0:
            flaky_tool_attempts[query]=1
            raise Exception("Simulated transient Network timeout.")
        return "Search results retrieved on second attempt for LangGraph and CrewAI."
    return f"Normal search results retrieved for: {query}"
   