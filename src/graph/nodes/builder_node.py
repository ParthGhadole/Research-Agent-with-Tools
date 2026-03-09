from src.util.prompts import BUILDER_PROMPT, DEFERRED_OPENING_PROMPT, DEFERRED_CLOSING_PROMPT
from src.util.llm_util import get_llm
from src.util.summary_util import format_global_summary_for_prompt
from src.util.models import Section
from src.graph.state import ResearchGraphState


async def builder_node(state: ResearchGraphState) -> ResearchGraphState:
    user_req = state["user_req"]
    target_order = state["current_build_order_index"] + 1
    
    # 1. Identify the current heading to process
    current_heading = next(
        (h for h in state["outline"].headings if h.build_order == target_order), 
        None
    )
    
    if current_heading is None:
        return None

    _llm = get_llm(provider=user_req.provider, model=user_req.model)

    # 2. Logic Branching: Standard vs. Deferred (Opening/Closing)
    if not current_heading.is_deferred:
        # Standard Builder Logic
        global_summary_formatted = format_global_summary_for_prompt(state["global_summary"])
        prompt = BUILDER_PROMPT
        
        builder_chain = prompt | _llm.with_structured_output(Section, include_raw=True)
        response = await builder_chain.ainvoke({
            "topic": user_req.topic,
            "heading": current_heading.heading,
            "sections_covered": global_summary_formatted["sections_covered"],
            "established_facts": global_summary_formatted["established_facts"],
            "narrative_position": global_summary_formatted["narrative_position"],
            "open_threads": global_summary_formatted["open_threads"],
            "next_section_expectation": global_summary_formatted["next_section_expectation"],
        })
    
    else:
        # 1. Determine deferred prompt type
        if current_heading.section_type == "deferred_opening":
            prompt = DEFERRED_OPENING_PROMPT
            # Identify which headings to exclude (other deferred openings)
            excluded_titles = {
                h.heading for h in state["outline"].headings 
                if h.is_deferred and h.section_type == "deferred_opening"
            }
        elif current_heading.section_type == "deferred_closing":
            prompt = DEFERRED_CLOSING_PROMPT
            # Only include context from sections with a lower position index
            excluded_titles = {
                s.heading for s in state["sections_completed"] 
                if s.position >= current_heading.position
            }
        else:
            raise ValueError("Unsupported deferred section type")

        # 2. Build compressed context by matching FactSheets to completed sections
        fact_sheet_map = {fs.heading: fs for fs in state["sections_fact_sheet"]}
        
        context_entries = []
        for section in state["sections_completed"]:
            if section.heading not in excluded_titles:
                fs = fact_sheet_map.get(section.heading)
                if fs:
                    entry = (
                        f"### {fs.heading}\n"
                        f"Summary: {fs.detailed_summary}\n"
                        f"Open Threads: {', '.join(fs.open_threads) if fs.open_threads else 'None'}"
                    )
                    context_entries.append(entry)

        formatted_context = "\n\n".join(context_entries)

        # 3. Invoke LLM
        deferred_chain = prompt | _llm.with_structured_output(Section, include_raw=True)
        response = await deferred_chain.ainvoke({
            "topic": user_req.topic,
            "heading": current_heading.heading,
            "completed_sections": formatted_context,
        })

    # 3. Validation and Output
    if response.get("parsing_error"):
        raise ValueError(f"LLM failed schema for {current_heading.heading}: {response['parsing_error']}")
    
    section_output = response["parsed"]
    
    # Manual assignment to ensure narrative order, not build order
    section_output.position = current_heading.position

    return {
        # **state,
        "pending_section": section_output
    }
