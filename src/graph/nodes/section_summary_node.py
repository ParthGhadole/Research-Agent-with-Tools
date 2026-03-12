# Summary Node

from src.util.prompts import SECTION_SUMMARIZER_PROMPT,GLOBAL_SUMMARY_UPDATER_PROMPT
from src.util.llm_util import get_llm
from src.graph.state import ResearchGraphState
from src.util.models import FactSheet, GlobalSummary
from src.util.summary_util import format_global_summary_for_prompt

async def section_summary_node(state : ResearchGraphState) -> ResearchGraphState:

    config = state["config"]
    draft = state["draft"]
    
    if draft.pending_section is None:
        raise ValueError("No pending section to summarize.")

    _llm = get_llm(provider=config.llm.provider, model=config.llm.model)

    summary_chain = SECTION_SUMMARIZER_PROMPT | _llm.with_structured_output(FactSheet, include_raw=True)
    global_summary_chain = GLOBAL_SUMMARY_UPDATER_PROMPT | _llm.with_structured_output(GlobalSummary, include_raw=True)
    
    current_section = draft.pending_section

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
    
    draft.current_build_order_index = draft.current_build_order_index +1 
    draft.sections_completed.append(current_section)
    draft.sections_fact_sheet.append(fact_sheet)
    draft.pending_section = None

    if state["config"].debug:
        global_log = state["global_log"]
        global_log.extend(
            SECTION_SUMMARIZER_PROMPT.format_messages(
                section_content=current_section.content
            )
        )
        global_log.append(summary_response["raw"])

        global_log.extend(
            GLOBAL_SUMMARY_UPDATER_PROMPT.format_messages(
                prev_sections_covered=formatted_prev["sections_covered"],
                prev_established_facts=formatted_prev["established_facts"],
                prev_narrative_position=formatted_prev["narrative_position"],
                prev_open_threads=formatted_prev["open_threads"],
                prev_next_section_expectation=formatted_prev["next_section_expectation"],
                fact_sheet=formatted_fact_sheet,
                outline=formatted_outline,
                current_heading=current_section.heading,
            )
        )
        global_log.append(global_summary_response["raw"])

        return {
            "global_log" : global_log,
            "draft" : draft,
            "global_summary" : global_summary_response["parsed"],
        }

    return {
        # **state,
        "draft" : draft,
        "global_summary" : global_summary_response["parsed"],

    }



async def test_section_summary_node(state : ResearchGraphState) -> ResearchGraphState:
    updates = await section_summary_node(state)
    state.update(updates)
    return state