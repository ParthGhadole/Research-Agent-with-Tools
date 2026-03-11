import os
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# Import your nodes and state
from src.graph.state import ResearchGraphState
from src.graph.nodes.assembly_node import assembly_node
from src.graph.nodes.input_node import input_node    
from src.graph.nodes.planner_node import planner_node
from src.graph.nodes.builder_node import builder_node
from graph.nodes.section_summary_node import section_summary_node
from src.api.deps import init_checkpointer

def autonomous_router(state: ResearchGraphState):
    # Check if the build index has reached the total number of headings
    if state["current_build_order_index"] >= len(state["outline"].headings):
        return "assembly"
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
    workflow.add_node("builder", builder_node)
    workflow.add_node("summary", section_summary_node)
    workflow.add_node("assembly", assembly_node)

    # 4. Define Logic
    workflow.add_edge(START, "input")
    workflow.add_edge("input", "planner")
    workflow.add_edge("planner", "builder")
    workflow.add_edge("builder", "summary")
    workflow.add_edge("assembly", END)
    
    workflow.add_conditional_edges(
        "summary",
        autonomous_router,
        {
            "builder": "builder",
            "assembly": "assembly"
        }
    )

    # 5. Compile and Return
    # Using the async checkpointer automatically enables async methods on the compiled app
    return workflow.compile(checkpointer=checkpointer)
