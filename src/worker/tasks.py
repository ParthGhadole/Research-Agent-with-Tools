from src.graph.workflow import create_workflow
from src.util.models import ResearchPayload


async def run_research_task(job_id: str, payload: ResearchPayload, app=None):
    """
    Executes the research graph. The assembler node within the graph 
    is responsible for populating the 'paper' and 'paper_path' keys.
    """
    # 1. Initialize State
    # Note: paper and paper_path start as None and are filled by the graph logic
    initial_state = {
    "messages": [],
    "user_req": payload.user_req,
    "confg": payload.config,
    "outline": None,
    "knowledge": None,
    "global_summary": None,
    "draft": None,
    "output": None
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