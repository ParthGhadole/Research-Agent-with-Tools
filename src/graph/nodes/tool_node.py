from src.graph.state import ResearchGraphState
from langchain_core.messages import ToolMessage
from src.tools import web_search_tool, web_crawl_tool
from src.util.models import RawResearchData, KnowledgeBase

async def tool_node(state: ResearchGraphState) -> ResearchGraphState:
    knowledge = state["knowledge"]
    messages = state["messages"]
    last_message = messages[-1]
    results = []
    # Check if the last message contains tool calls
    if last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            # Route to your specific tool logic
            if tool_name == "web_search_tool":
                result = await web_search_tool.ainvoke(tool_args["query"])
            elif tool_name == "web_crawl_tool":
                result = await web_crawl_tool.ainvoke(tool_args["url"])

                new_data = RawResearchData(
                    tool_id=tool_call["id"],
                    tool_name="web_crawl_tool",
                    url=result.get("url", ""),
                    raw_content= result.get("url_content", ""),
                    len_content =len(result.get("url_content", "")),
                )

                knowledge.raw_knowledge.append(new_data)
                result = {
                    "content": "Content successfully crawled and saved to KnowledgeBase",
                    "url": result.get("url", ""),
                    "url_content_length (in characters)": len(result.get("url_content", "")),
                }
            else:
                result = "Error: Tool not found."

            # Append the result as a ToolMessage to the state
            results.append(ToolMessage(
                content=str(result), 
                tool_call_id=tool_call["id"]
            ))

    messages.extend(results)

    return {
        "messages": messages,
        "knowledge": knowledge
    }


async def test_tool_node(state : ResearchGraphState) -> ResearchGraphState:
    updates = await tool_node(state)
    state.update(updates)
    return state