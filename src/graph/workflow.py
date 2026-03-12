import os
from langgraph.graph import StateGraph, START, END
from src.graph.state import ResearchGraphState
from langchain_core.messages import AIMessage
from src.graph.nodes import (
    input_node,
    planner_node,
    builder_node, 
    section_summary_node, 
    assembly_node, 
    context_summary_node, 
    tool_node,
    research_node
)
from src.api.deps import init_checkpointer

def autonomous_router_builder_summary_assembly_path(state: ResearchGraphState):
    if state["draft"].current_build_order_index >= len(state["outline"].headings):
        return "assembly"
    return "builder"

def autonomous_router_planner_research_builder_path(state: ResearchGraphState):
    if state["config"].graph.research_enabled:
        return "research"
    return "builder"


def autonomous_router_research_context_tool_path(state: ResearchGraphState):
    if not state.get("messages"):
        return "builder"
        
    last_message = state["messages"][-1]
    
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tool"

    if state["knowledge"].raw_knowledge:
        return "knowledge_summary"
    
    return "builder"
async def create_workflow(checkpointer=None):
    """
    Factory function to initialize and compile the workflow.
    Now supports async initialization.
    """

    # 1. Initialize checkpointer if not provided
    if checkpointer is None:
        checkpointer = await init_checkpointer()

    # 2. Build the Graph
    workflow = StateGraph(ResearchGraphState)

    # 3. Add Nodes
    workflow.add_node("input", input_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("research", research_node)
    workflow.add_node("tool", tool_node)
    workflow.add_node("knowledge_summary", context_summary_node)
    workflow.add_node("builder", builder_node)
    workflow.add_node("section_summary", section_summary_node)
    workflow.add_node("assembly", assembly_node)

    # 4. Define Logic

    workflow.add_edge(START, "input")
    workflow.add_edge("input", "planner")

    workflow.add_conditional_edges(
        "planner",
        autonomous_router_planner_research_builder_path,
        {
            "research": "research",
            "builder": "builder"
        }
    )
    workflow.add_conditional_edges(
        "research",
        autonomous_router_research_context_tool_path,
        {
            "knowledge_summary": "knowledge_summary",
            "tool": "tool",
            "builder": "builder"
        }
    )
    workflow.add_edge("tool", "research")
    workflow.add_edge("knowledge_summary", "builder")
    workflow.add_edge("builder", "section_summary")
    workflow.add_conditional_edges(
        "section_summary",
        autonomous_router_builder_summary_assembly_path,
        {
            "builder": "builder",
            "assembly": "assembly"
        }
    )
    workflow.add_edge("assembly", END)

    # 5. Compile and Return
    # Using the async checkpointer automatically enables async methods on the compiled app
    return workflow.compile(checkpointer=checkpointer)
