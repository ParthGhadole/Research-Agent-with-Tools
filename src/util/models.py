from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from typing import List
from pydantic import BaseModel, Field

class LLMConfig(BaseModel):
    """The configuration for the LLM"""
    model: str = "gemini-2.5-flash-lite"
    provider: str = "gemini"
    temperature: Optional[float] = 0.5
    max_tokens: Optional[int] = 4000
    
class GraphConfig(BaseModel):
    """The configuration for the Graph"""
    research_enabled: Optional[bool] = False
    max_web_search_limit: Optional[int] = 1
    max_web_crawl_limit: Optional[int] = 10
    keep_raw_crawl: Optional[bool] = True

class ResearchRequest(BaseModel):
    """The initial user input schema."""
    topic: str
    description: str
    points_to_include: List[str]
    min_sections: int = 5
    compulsory_headings: List[str]

class GlobalConfig(BaseModel):
    llm: LLMConfig = LLMConfig()
    graph: GraphConfig = GraphConfig()
    debug: bool = False

class ResearchPayload(BaseModel):
    user_req: ResearchRequest
    config: GlobalConfig

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

class RawResearchData(BaseModel):
    tool_id: str =""
    tool_name: str = "web_crawl"
    url: str = "about:blank"
    raw_content: Optional[str] = None
    len_content: int = 0

class DetailedKnowledge(BaseModel):
    tool_id: str
    tool_name: str
    url: str
    summary: str
    raw_content: Optional[str] = None
    relevant_headings: List[str] = Field(default_factory=list)

class KnowledgeSummary(BaseModel):
    summary: str
    relevant_headings: List[str] = Field(default_factory=list)

class KnowledgeBase(BaseModel):
    raw_knowledge: List[RawResearchData] = Field(default_factory=list)
    detailed_knowledge: Dict[str, DetailedKnowledge] = Field(default_factory=dict)
    knowledge_map: Dict[str, List[str]] = Field(default_factory=dict)

class ResearchDraft(BaseModel):
    sections_completed: Optional[List[Section]]
    sections_fact_sheet: Optional[List[FactSheet]]
    pending_section: Optional[Section]
    current_build_order_index: int

class ResearchOutput(BaseModel):
    paper: Optional[ResearchPaper]
    paper_path: Optional[str]

