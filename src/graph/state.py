from src.util.models import (
    ResearchRequest,
    Outline,
    GlobalSummary,
    Section,
    FactSheet,
    ResearchPaper
)

from typing import Annotated, List, Optional, Union
from typing_extensions import TypedDict
import operator
from langchain_core.messages import BaseMessage
# Graph State
class ResearchGraphState(TypedDict):
    messages: List[BaseMessage]
    user_req: ResearchRequest
    outline: Outline
    global_summary: GlobalSummary
    sections_completed: Optional[List[Section]]
    sections_fact_sheet: Optional[List[FactSheet]]
    pending_section: Optional[Section]
    human_feedback: Optional[str]
    current_build_order_index: int
    # references: Optional[List[str]]
    paper: Optional[ResearchPaper]
    paper_path: Optional[str]

async def get_detailed_research_status(state: ResearchGraphState) -> dict:
    """
    Analyzes the specific state transitions between nodes to provide
    a high-fidelity status update.
    """
    # 1. Extraction of core variables
    user_req = state.get("user_req")
    outline = state.get("outline")
    completed = state.get("sections_completed") or []
    pending = state.get("pending_section")
    current_idx = state.get("current_build_order_index", 0)
    paper = state.get("paper")

    # 2. Phase: Initialization (input_node)
    if not user_req:
        return {
            "phase": "Initialization",
            "status": "Waiting for research request...",
            "progress": 0
        }

    # 3. Phase: Planning (planner_node)
    if not outline or not outline.headings:
        return {
            "phase": "Planning",
            "status": f"Generating research outline for: {user_req.topic}",
            "progress": 10
        }

    # 4. Phase: Looping (builder_node & summary_node)
    total_sections = len(outline.headings)
    
    # Check if we are still within the build loop
    if current_idx < total_sections:
        # Sort headings by build order to find the current target
        build_sequence = sorted(outline.headings, key=lambda h: h.build_order)
        current_heading_obj = build_sequence[current_idx]
        heading_text = current_heading_obj.heading
        
        # Calculate progress: Base 15% + percentage of sections done
        progress_base = 15
        progress_per_section = 75 / total_sections
        current_progress = int(progress_base + (current_idx * progress_per_section))

        # Check if builder has finished but summary hasn't (State: pending_section exists)
        if pending:
            return {
                "phase": "Summarizing",
                "status": f"Summarizing and updating global context for: '{heading_text}'",
                "progress": current_progress + int(progress_per_section * 0.5),
                "current_section": heading_text,
                "section_count": f"{current_idx + 1}/{total_sections}"
            }
        
        # Default: The builder is currently working
        status_msg = f"Writing section: '{heading_text}'"
        if current_heading_obj.is_deferred:
            status_msg = f"Writing deferred section ({current_heading_obj.section_type}): '{heading_text}'"
            
        return {
            "phase": "Writing",
            "status": status_msg,
            "progress": current_progress,
            "current_section": heading_text,
            "section_count": f"{current_idx + 1}/{total_sections}"
        }

    # 5. Phase: Finalization (assembly_node)
    if paper:
        return {
            "phase": "Completed",
            "status": f"Research complete. Paper saved to {state.get('paper_path')}",
            "progress": 100
        }

    return {
        "phase": "Assembly",
        "status": "Assembling all sections into narrative order and exporting...",
        "progress": 95
    }