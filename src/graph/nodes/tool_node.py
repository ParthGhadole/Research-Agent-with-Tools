from src.graph.state import ResearchGraphState
from langchain_core.messages import ToolMessage

def tool_node(state: ResearchGraphState) -> ResearchGraphState:
    messages = state["messages"]
    last_message = messages[-1]
    results = []
    # Check if the last message contains tool calls
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            # # Route to your specific tool logic
            # if tool_name == "web_search":
            #     result = web_search_tool.run(tool_args["query"])
            # elif tool_name == "academic_search":
            #     result = academic_search_tool.run(tool_args["query"])
            # else:
            #     result = "Error: Tool not found."

            # # Append the result as a ToolMessage to the state
            # results.append(ToolMessage(
            #     content=str(result), 
            #     tool_call_id=tool_call["id"]
            # ))

    return {
        "messages": messages
    }