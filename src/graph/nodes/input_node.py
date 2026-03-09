from src.graph.state import ResearchGraphState
from src.util.models import GlobalSummary

async def input_node(state : ResearchGraphState) -> ResearchGraphState:
    req = state["user_req"]

    if len(req.topic) < 5:
        raise ValueError("Topic is too short for a research paper.")
    globalSummary = GlobalSummary(
        sections_covered=[],
        established_facts="",
        narrative_position="",
        open_threads=[],
        next_section_expectation=""
    )
    return {
        # **state,
        "global_summary": globalSummary,
        "sections_completed": [],
        "sections_fact_sheet": []
    }