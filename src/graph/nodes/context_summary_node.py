from src.graph.state import ResearchGraphState

async def context_summary_node(state : ResearchGraphState) -> ResearchGraphState:
    knowledge = state['knowledge']
    len_unprocessed = len(knowledge.raw_knowledge)

    
    return {
        
    }