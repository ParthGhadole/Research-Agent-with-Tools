from src.graph.workflow import create_workflow
from src.util.models import ResearchRequest


async def run_research_task(job_id: str, request_data: ResearchRequest, app=None):
    """
    Executes the research graph. The assembler node within the graph 
    is responsible for populating the 'paper' and 'paper_path' keys.
    """
    # 1. Initialize State
    # Note: paper and paper_path start as None and are filled by the graph logic
    initial_state = {
        "user_req": request_data,
        "outline": None,
        "global_summary": None,
        "sections_completed": [],
        "sections_fact_sheet": [],
        "pending_section": None,
        "human_feedback": None,
        "current_build_order_index": 0,
        "paper": None,
        "paper_path": None
    }

    # 2. Configuration for persistence
    config = {
        "configurable": {"thread_id": job_id},
        "recursion_limit": 150 
    }

    try:
       
        final_state = await app.ainvoke(input=initial_state, config=config)

        paper = final_state.get("paper")
        
        return paper

    except Exception as e:
        raise e