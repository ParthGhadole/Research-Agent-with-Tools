from pydantic import BaseModel, Field
from typing import List, Optional


class ResearchRequest(BaseModel):
    """The initial user input schema."""
    topic: str
    description: str
    points_to_include: List[str]
    min_sections: int = 5
    compulsory_headings: List[str]
    search_enabled: bool = False
    min_search_limit: int = 1
    model: str = ""
    provider: str = ""


# class SectionHeading(BaseModel):
#     """Schema for a single heading in the roadmap, guiding the AI's workflow."""
#     heading: str = Field(description="The clear, descriptive title of this specific section.")
#     position: int = Field(description="The physical location in the final document (e.g., 1 for Intro or abstract, 10 for Conclusion).")
#     build_order: int = Field(description="The sequence index for the agent to build the paper in.")
#     section_type: str = Field(description="Category of the section: 'deferred_opening', 'normal', or 'deferred_closing'.")
#     is_deferred: bool = Field(default=False, description="True if this section requires data from other sections before it can be finalized.")
class SectionHeading(BaseModel):
    """Schema for a single heading in the roadmap."""
    
    heading: str
    position: int
    build_order: int
    section_type: str
    is_deferred: bool = False


class Outline(BaseModel):
    """Schema for the research roadmap."""
    headings: List[SectionHeading]


class FactSheet(BaseModel):
    """Schema for the detailed per-section summary."""
    heading: str = Field(description="The clear, descriptive title of this specific section.")
    detailed_summary: str = Field(description="An extensive and detailed summary of the section content, arguments, and data presented.")
    open_threads: List[str] = Field(description="Unresolved questions or promises made to the reader in this section.")


class Section(BaseModel):
    """Schema for an individual research section."""
    heading: str = Field(description="The exact title of the section.")
    position: int = Field(description="Final position in the assembled paper.")
    content: str = Field(description="The full Markdown content, starting with ## Heading.")

class GlobalSummary(BaseModel):
    """Schema for the rolling paper state tracker passed to the Builder."""
    sections_covered: List[str] = Field(description="Ordered list of headings built so far.")
    established_facts: str = Field(description="Compressed bullets of locked-in definitions, arguments, and data.")
    narrative_position: str = Field(description="1-2 sentences on where the paper stands in the story arc.")
    open_threads: List[str] = Field(description="Curated live threads — resolved ones are retired each iteration.")
    next_section_expectation: str = Field(description="2-3 sentences max on what the next Builder call must deliver.")


class ResearchPaper(BaseModel):
    """The final aggregated research document."""
    topic: str
    content: List[Section]