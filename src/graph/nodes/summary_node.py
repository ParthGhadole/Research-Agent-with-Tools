# Summary Node

from src.util.prompts import SECTION_SUMMARIZER_PROMPT,GLOBAL_SUMMARY_UPDATER_PROMPT
from src.util.llm_util import get_llm
from src.graph.state import ResearchGraphState
from src.util.models import FactSheet, GlobalSummary
from src.util.summary_util import format_global_summary_for_prompt

async def summary_node(state : ResearchGraphState) -> ResearchGraphState:

    if state["pending_section"] is None:
        return None

    user_req = state["user_req"]
    sections_completed = state["sections_completed"]
    sections_fact_sheet = state["sections_fact_sheet"]

    _llm = get_llm(provider=user_req.provider, model=user_req.model)
    summary_chain = SECTION_SUMMARIZER_PROMPT | _llm.with_structured_output(FactSheet, include_raw=True)
    global_summary_chain = GLOBAL_SUMMARY_UPDATER_PROMPT | _llm.with_structured_output(GlobalSummary, include_raw=True)
    current_section = state["pending_section"]
    summary_response = await summary_chain.ainvoke({
        "section_content": current_section.content
    })
    
    if (summary_response.get("parsing_error")):
        raise ValueError(f"LLM failed to follow the schema: {summary_response['parsing_error']}")

    fact_sheet = summary_response["parsed"]

    formatted_prev = format_global_summary_for_prompt(state["global_summary"])

    formatted_outline = "\n".join(
        [f"pos={h.position} build_order={h.build_order} deferred={h.is_deferred} → {h.heading}"
         for h in sorted(state["outline"].headings, key=lambda h: h.position)]
    )

    formatted_fact_sheet = (
        f"detailed_summary:\n{fact_sheet.detailed_summary}\n\n"
        f"open_threads:\n" + "\n".join(f"- {t}" for t in fact_sheet.open_threads)
        if fact_sheet.open_threads else
        f"detailed_summary:\n{fact_sheet.detailed_summary}\n\nopen_threads: None"
    )

    global_summary_response = await global_summary_chain.ainvoke({
        "prev_sections_covered": formatted_prev["sections_covered"],
        "prev_established_facts": formatted_prev["established_facts"],
        "prev_narrative_position": formatted_prev["narrative_position"],
        "prev_open_threads": formatted_prev["open_threads"],
        "prev_next_section_expectation": formatted_prev["next_section_expectation"],
        "fact_sheet": formatted_fact_sheet,
        "outline": formatted_outline,
        "current_heading": current_section.heading,
    })

    if global_summary_response.get("parsing_error"):
        raise ValueError(f"LLM failed to follow the schema: {global_summary_response['parsing_error']}")
    
    idx = state["current_build_order_index"]+1
    sections_completed.append(current_section)
    sections_fact_sheet.append(fact_sheet)
    return {
        # **state,
        "sections_completed" : sections_completed,
        "sections_fact_sheet" : sections_fact_sheet,
        "pending_section" : None,
        "global_summary" : global_summary_response["parsed"],
        "current_build_order_index" : idx
    }