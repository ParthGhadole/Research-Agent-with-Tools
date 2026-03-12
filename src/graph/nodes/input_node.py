from src.graph.state import ResearchGraphState
from src.util.models import GlobalSummary,KnowledgeBase,ResearchDraft

async def input_node(state : ResearchGraphState) -> ResearchGraphState:
    req = state["user_req"]

    if len(req.topic) < 5:
        raise ValueError("Topic is too short for a research paper.")
    
    if req.min_sections < 4:
        raise ValueError("Minimum number of sections should be at least 4.")
    
    if req.min_sections > 10:
        raise ValueError("Maximum number of sections should be at most 10.")
    
    if req.min_sections < len(req.compulsory_headings):
        raise ValueError("Minimum number of sections should be at least the number of compulsory headings.")
    
    globalSummary = GlobalSummary(
        sections_covered=[],
        established_facts="",
        narrative_position="",
        open_threads=[],
        next_section_expectation=""
    )
    knowledge = KnowledgeBase(
        raw_knowledge=[],
        detailed_knowledge={},
        knowledge_map={}
    )
    draft = ResearchDraft(
        sections_completed=[],
        sections_fact_sheet=[],
        pending_section=None,
        current_build_order_index=-1
    )
    return {
        "global_log": [],
        "global_summary": globalSummary,
        "knowledge": knowledge,
        "draft": draft
    }

async def test_input_node(state : ResearchGraphState) -> ResearchGraphState:
    updates = await input_node(state)
    state.update(updates)
    return state

