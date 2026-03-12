from src.util.models import (
    ResearchRequest,
    Outline,
    GlobalSummary,
    GlobalConfig,
    KnowledgeBase,
    ResearchDraft,
    ResearchOutput
)
from pydantic import BaseModel
from typing import  List, Optional, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
import json
import pickle
from pathlib import Path

# Graph State
class ResearchGraphState(TypedDict):
    global_log: List[BaseMessage]
    messages: List[BaseMessage]
    user_req: ResearchRequest
    config: GlobalConfig
    outline: Outline
    knowledge: KnowledgeBase
    global_summary: GlobalSummary
    draft: Optional[ResearchDraft]
    output: Optional[ResearchOutput]

async def print_state_as_json(state: Any):
    """
    Safely serializes a state object (dict or Pydantic model) to a 
    formatted JSON string and prints it.
    """
    def json_serializer(obj):
        # If it's a Pydantic model, convert to dict
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        # Fallback for non-serializable types (like datetime)
        return str(obj)

    # Use default=json_serializer to handle nested Pydantic objects
    json_output = json.dumps(state, indent=4, default=json_serializer)
    print(json_output)

async def save_state_as_json(state: Any, filepath: str):
    """
    Serializes a state object to a JSON file, creating the directory 
    path if it does not exist.
    """
    def json_serializer(obj):
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return str(obj)

    # Convert to Path object
    path = Path(filepath)
    
    # Create the directory structure if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write the file
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4, default=json_serializer)
async def save_as_pkl(obj, filename: str):
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)

async def load_as_pkl(filename: str):
    with open(filename, 'rb') as f:
        return pickle.load(f)
    



from typing import Dict, Any

def _get_total_sections(state: dict) -> int:
    outline = state.get("outline")
    if outline and hasattr(outline, "headings"):
        return len(outline.headings)
    return 0

def _get_next_heading(state: dict) -> str:
    outline = state.get("outline")
    draft = state.get("draft")
    
    if not outline or not hasattr(outline, "headings") or not draft:
        return "None"
        
    target_order = draft.current_build_order_index + 1
    for h in outline.headings:
        if h.build_order == target_order:
            return h.heading
    return "None"

def _get_active_node_hint(state: dict) -> str:
    if state.get("error"):
        return "ERROR_OCCURRED"
        
    if state.get("output"):
        return "END"
        
    draft = state.get("draft")
    outline = state.get("outline")
    
    if not outline:
        if not state.get("user_req"):
            return "input_node"
        return "planner_node"
        
    if draft:
        total = _get_total_sections(state)
        if draft.current_build_order_index >= total:
            return "assembly_node"
            
        if draft.pending_section:
            return "section_summary_node"
            
        if draft.current_build_order_index >= 0:
            return "builder_node"
            
        # If build order is 0 or -1 but we have an outline, we are in research/tool phase
        knowledge = state.get("knowledge")
        if knowledge and getattr(knowledge, "raw_knowledge", None) and not getattr(knowledge, "detailed_knowledge", None):
            return "context_summary_node"
            
        messages = state.get("messages", [])
        if messages and hasattr(messages[-1], "tool_calls") and messages[-1].tool_calls:
            return "tool_node"
            
        return "research_node"
        
    return "unknown"

def _determine_phase(state: dict) -> str:
    if state.get("error"):
        return "FAILED"
        
    if state.get("output"):
        return "COMPLETED"
        
    draft = state.get("draft")
    if not draft:
        if state.get("outline"):
            return "PLANNING_COMPLETE"
        return "INITIALIZATION_OR_PLANNING"
        
    total_sections = _get_total_sections(state)
    current_idx = draft.current_build_order_index
    
    if current_idx >= total_sections:
        return "ASSEMBLY"
        
    if draft.pending_section:
        return "SUMMARIZING_SECTION"
        
    if current_idx > 0 or (current_idx == 0 and draft.sections_completed):
        return "WRITING_SECTION"
        
    if current_idx <= 0:
        knowledge = state.get("knowledge")
        if knowledge and getattr(knowledge, "raw_knowledge", None) and not getattr(knowledge, "detailed_knowledge", None):
            return "KNOWLEDGE_MAPPING"
        return "RESEARCH_AND_RETRIEVAL"
        
    return "UNKNOWN_PHASE"

def _calculate_total_progress(state: dict) -> float:
    # Progress calculation remains based on where the process was when it stopped/failed.
    # 0-5%: Init & Planning
    # 5-20%: Research & Mapping
    # 20-95%: Writing (Distributed)
    # 95-100%: Assembly & Output
    
    if state.get("output"):
        return 100.0
        
    draft = state.get("draft")
    if not draft:
        if state.get("outline"):
            return 5.0
        return 0.0
        
    total_sections = _get_total_sections(state)
    if total_sections == 0:
        return 5.0
        
    current_idx = draft.current_build_order_index
    
    # If we finished all sections but aren't done yet
    if current_idx >= total_sections:
        return 95.0
        
    # If we are in the initial research loop
    if current_idx <= 0 and not draft.sections_completed:
        knowledge = state.get("knowledge")
        if knowledge and getattr(knowledge, "raw_knowledge", None):
            if getattr(knowledge, "detailed_knowledge", None):
                return 18.0
            return 12.0
        return 8.0
        
    # Writing phase
    progress_per_section = 75.0 / total_sections
    base_progress = 20.0 + (current_idx * progress_per_section)
    
    if draft.pending_section:
        base_progress += (progress_per_section * 0.5)
        
    return round(base_progress, 2)

async def get_detailed_research_status(state: dict) -> Dict[str, Any]:
    """
    Returns a high-fidelity state object including sub-phase progress,
    queue status, knowledge repository health, and error tracking.
    """
    total_sections = _get_total_sections(state)
    draft = state.get("draft")
    knowledge = state.get("knowledge")
    error_val = state.get("error")
    
    current_idx = draft.current_build_order_index if draft else -1
    pending_section = draft.pending_section if draft else None
    
    raw_count = len(knowledge.raw_knowledge) if knowledge and hasattr(knowledge, "raw_knowledge") else 0
    detailed_count = len(knowledge.detailed_knowledge) if knowledge and hasattr(knowledge, "detailed_knowledge") else 0
    
    return {
        "execution_state": {
            "phase": _determine_phase(state),
            "progress_percent": _calculate_total_progress(state),
            "possible_active_node_hint": _get_active_node_hint(state),
            "has_error": error_val is not None,
            "error_message": str(error_val) if error_val else None,
            "section_tracker": {
                "current_index": current_idx,
                "total_sections": total_sections,
                "is_summarizing": pending_section is not None
            }
        },
        "knowledge_state": {
            "raw_entries_collected": raw_count,
            "synthesized_entries": detailed_count,
        },
        "drafting_state": {
            "completed_sections_count": len(draft.sections_completed) if draft and hasattr(draft, "sections_completed") else 0,
            "next_target_heading": _get_next_heading(state),
            "pending_build_order": current_idx + 1 if current_idx + 1 <= total_sections else "None"
        },
        "memory_state": {
            "global_log_size": len(state.get("global_log", [])),
            "messages_count": len(state.get("messages", [])),
            "has_final_output": state.get("output") is not None
        }
    }