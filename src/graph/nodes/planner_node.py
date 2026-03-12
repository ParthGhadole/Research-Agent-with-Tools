# Planner Node
from src.util.models import Outline, SectionHeading
from src.util.prompts import PLANNER_PROMPT
from src.util.llm_util import get_llm
from src.graph.state import ResearchGraphState
from dotenv import load_dotenv
load_dotenv()

def fix_build_order(headings: list[SectionHeading]) -> tuple[list[SectionHeading], bool]:
    """If build_order is not sequential from 1, fix it by sorting and reassigning."""
    orders = sorted(s.build_order for s in headings)
    expected = list(range(1, len(headings) + 1))
    if orders == expected:
        return headings, False  # no fix needed

    # Sort by existing build_order and reassign 1..N
    sorted_headings = sorted(headings, key=lambda s: s.build_order)
    for i, section in enumerate(sorted_headings, start=1):
        section.build_order = i
    return sorted_headings, True


def validate_position_sequence(headings: list[SectionHeading]) -> bool:
    """Check all positions from 1 to max are present with no gaps or duplicates."""
    positions = [s.position for s in headings]
    expected = list(range(1, len(headings) + 1))
    return sorted(positions) == expected


async def planner_node(state: ResearchGraphState) -> ResearchGraphState:
    user_req = state["user_req"]
    llm_config = state["config"].llm
    draft = state["draft"]
    llm = get_llm(provider=llm_config.provider, model=llm_config.model)

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
    headings = parsed_outline.headings

    # ── Position check ────────────────────────────────────────────────────────
    if not validate_position_sequence(headings):
        positions = sorted(s.position for s in headings)
        raise ValueError(f"Position sequence is invalid: {positions}. Expected 1 to {len(headings)}.")

    # ── Build order check + auto-fix ──────────────────────────────────────────
    headings, was_fixed = fix_build_order(headings)
    if was_fixed:
        print(f"⚠ build_order was not sequential — auto-corrected by sorting and reassigning 1 to {len(headings)}.")
        parsed_outline.headings = sorted(headings, key=lambda s: s.position)
        
    draft.current_build_order_index = 0

    if state["config"].debug:
        global_log = state["global_log"]
        global_log.extend(
            PLANNER_PROMPT.format_messages(
                topic=user_req.topic,
                description=user_req.description,
                compulsory_headings=user_req.compulsory_headings,
                points_to_include=user_req.points_to_include,
                min_sections=user_req.min_sections
            )
        )
        global_log.append(response["raw"])


        return{
            "global_log": global_log,
            "outline": parsed_outline,
            "draft": draft
        }
    
    return {
        "outline": parsed_outline,
        "draft": draft
    }


async def test_planner_node(state : ResearchGraphState) -> ResearchGraphState:
    updates = await planner_node(state)
    state.update(updates)
    return state
