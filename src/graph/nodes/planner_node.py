# Planner Node
from src.util.models import ResearchRequest, Outline
from src.util.prompts import PLANNER_PROMPT
from src.util.llm_util import get_llm
from src.graph.state import ResearchGraphState
from dotenv import load_dotenv
load_dotenv()
async def planner_node(state: ResearchGraphState)->ResearchGraphState:
    user_req = state["user_req"]

    llm = get_llm(provider="gemini", model= "gemini-2.5-flash")


    planner_chain = PLANNER_PROMPT | llm.with_structured_output(Outline, include_raw=True)

    print(f"Generating research outline for: {user_req.topic}...")

    response = await planner_chain.ainvoke({
        "topic": user_req.topic,
        "description": user_req.description,
        "compulsory_headings": user_req.compulsory_headings,
        "points_to_include": user_req.points_to_include,
        "min_sections": user_req.min_sections
    })

    if response.get("parsing_error"):
        raise ValueError(f"LLM failed to follow the schema: {response['parsing_error']}")
    
    parsed_outline = response["parsed"]

    

    # # 1. Normalize Build Order (Writing Sequence)
    # # Sort by the LLM's suggested build order and re-index 1..N
    # sorted_by_build = sorted(parsed_outline.headings, key=lambda h: h.build_order)
    # for i, heading in enumerate(sorted_by_build, start=1):
    #     heading.build_order = i

    # # Update the outline object with the corrected headings
    # parsed_outline.headings = sorted_by_build


    return {
        # **state,
        "outline": parsed_outline,
        "current_build_order_index": 0,
        "sections_completed": [],
        "sections_fact_sheet": []
        
    }

