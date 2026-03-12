from src.graph.state import ResearchGraphState
from src.util.prompts import RESEARCH_PROMPT
from langchain_core.messages import HumanMessage
from src.util.llm_util import get_llm
from src.tools import web_search_tool,web_crawl_tool

async def research_node(state : ResearchGraphState) -> ResearchGraphState:
    user_req = state['user_req']
    graph_config = state['config'].graph
    llm_config = state['config'].llm
    if graph_config.research_enabled == False:
        raise Exception("Graph research is disabled")
    Flag = False
    msg = state['messages']
    if len(msg) == 0:
        Flag = True
        msg.append(HumanMessage(content=f"Start the research process for: {user_req.topic}"))        
    
    prompt_input = RESEARCH_PROMPT.format_messages(
        topic= user_req.topic,
        max_search=graph_config.max_web_search_limit,
        max_crawl=graph_config.max_web_crawl_limit,
        history=msg
        )

    llm = get_llm(provider=llm_config.provider, model=llm_config.model).bind_tools(tools=[web_search_tool,web_crawl_tool])
    response = await llm.ainvoke(prompt_input)
    msg.append(response)

    if state["config"].debug:
        global_log = state["global_log"]
        if Flag:
            global_log.extend(prompt_input)
        global_log.append(response)
        return {
            "global_log": global_log,
            "messages": msg
        }
    
    return {
        "messages": msg
    }


async def test_research_node(state : ResearchGraphState) -> ResearchGraphState:
    updates = await research_node(state)
    state.update(updates)
    return state