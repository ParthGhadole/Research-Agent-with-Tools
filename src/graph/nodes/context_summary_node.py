from src.graph.state import ResearchGraphState
from src.util.prompts import CONTEXT_SUMMARY_PROMPT
from src.util.models import KnowledgeSummary,DetailedKnowledge
from src.util.llm_util import get_llm
from collections import defaultdict

async def context_summary_node(state : ResearchGraphState) -> ResearchGraphState:
    knowledge = state['knowledge']
    outline = state['outline']
    config = state['config']
    _llm = get_llm(provider=config.llm.provider, model=config.llm.model)

    if state["config"].debug:
        global_log = state["global_log"]


    new_detailed_knowledge = {}
    knowledge_map = defaultdict(list, knowledge.knowledge_map)

    for data in knowledge.raw_knowledge:

        if data.len_content < 10:
            continue
        
        prompt_input = CONTEXT_SUMMARY_PROMPT.format_messages(
            outline=outline, 
            raw_content=data.raw_content
        )

        response = await _llm.with_structured_output(
            KnowledgeSummary, 
            include_raw=True
        ).ainvoke(prompt_input)
        
        summary_obj = response["parsed"]

        new_data = DetailedKnowledge(
            tool_id=data.tool_id,
            tool_name=data.tool_name,
            url=data.url,
            summary=summary_obj.summary,
            relevant_headings=summary_obj.relevant_headings
        )

        if state["config"].graph.keep_raw_crawl == True:
            new_data.raw_content = data.raw_content
        
        new_detailed_knowledge[data.tool_id] = new_data

        for heading in summary_obj.relevant_headings:
            if data.tool_id not in knowledge_map[heading]:
                knowledge_map[heading].append(data.tool_id)

        if state["config"].debug:
            global_log.extend(prompt_input)
            global_log.append(response["raw"])

    knowledge.detailed_knowledge =  knowledge.detailed_knowledge | new_detailed_knowledge
    knowledge.knowledge_map = dict(knowledge_map)

    if config.graph.keep_raw_crawl == False and config.debug == False:
        knowledge.raw_knowledge = []
    
    if state["config"].debug:
        return {
            "global_log": global_log,
            "knowledge": knowledge
        }

    return {
        "knowledge": knowledge
    }

async def test_context_summary_node(state : ResearchGraphState) -> ResearchGraphState:
    updates = await context_summary_node(state)
    state.update(updates)
    return state