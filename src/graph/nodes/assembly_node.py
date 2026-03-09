
from src.graph.state import ResearchGraphState
from src.util.models import ResearchPaper, ResearchRequest, Section
from typing import List
from pathlib import Path

import uuid


def export_paper(paper: ResearchPaper) -> None:
    """Exports the ResearchPaper to a markdown file."""

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    safe_topic = "".join(c if c.isalnum() or c in " _-" else "" for c in paper.topic)
    safe_topic = safe_topic.strip().replace(" ", "_")[:80]
    file_path = output_dir / f"{safe_topic +"_"+ str(uuid.uuid4())}.md"

    lines = [f"# {paper.topic}\n\n"]
    for section in paper.content:
        lines.append(section.content)
        lines.append("\n\n")

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return str(file_path)

def assembly_node(state: ResearchGraphState) -> ResearchGraphState:    
    user_req = state["user_req"]
    outline = state["outline"]  # Accessing the Outline model from state
    completed_sections = state["sections_completed"]

    # 1. Create a lookup dictionary using the .heading and .position fields
    # We use .heading because your SectionHeading schema uses that field name
    section_position_map = {
        section.heading: section.position 
        for section in outline.headings
    }

    # 2. Sort completed_sections based on the defined document position
    # s.title in your Section object should match section.heading in your Outline
    sorted_sections = sorted(
        completed_sections, 
        key=lambda s: section_position_map.get(s.heading, 999)
    )
    
    paper = ResearchPaper(
        topic=user_req.topic,
        content=sorted_sections
    )

    # Export the paper to your desired format (Markdown/PDF)
    path = export_paper(paper)

    return {
        # **state,
        "paper": paper,
        "paper_path": path
    }
