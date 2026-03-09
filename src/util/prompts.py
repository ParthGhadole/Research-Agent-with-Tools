from langchain_core.prompts import ChatPromptTemplate


# works but has /n in the raw response with // as well
# PLANNER_PROMPT = ChatPromptTemplate.from_messages([
#     ("system", """You are a Research Architect. Your task is to design a comprehensive research paper outline that transforms technical points into a logical narrative.

# UNIVERSAL STRUCTURAL FLOW:
# Your outline must follow this logical progression:
# 1. THE FOUNDATION: Abstract and an Introduction that provides the "Hook" and significance of the topic.
# 2. THE MECHANISMS: Core theories, fundamental structures, or underlying principles.
# 3. THE CONTEXT: Comparative analysis, historical background, or benchmarking against standards.
# 4. THE CHALLENGE: Critical examination of problems, limitations, or existing gaps.
# 5. THE TECHNICAL ANALYSIS: Data-driven solutions, performance metrics, or specialized findings.
# 6. THE APPLICATION: Practical implementation, industrial constraints, or real-world scalability.
# 7. THE SYNTHESIS: Conclusion including summary of findings and Future Perspectives.

# MANDATORY REQUIREMENTS:
# 1. Include ALL required headings: {compulsory_headings}
# 2. Try to Integrate ALL key points logically within the flow: {points_to_include}
# 3. Generate at least {min_sections} total sections but if the topic and description are too complexx to be covered in {min_sections} sections, generate many more.

# DESIGN PRINCIPLES:
# - Use clear, specific, and descriptive phrases for headings.
# - Ensure a "Story Arc" where each section builds upon the previous one.
# - Maintain a balance between foundational theory and practical application.

# SECTION METADATA RULES:
# - position: reflects the final reading order of the paper. 
# - is_deferred: Analyse each section heading semantically. Set True for any section that requires the full paper to be written before it can be generated — such as Abstract, Executive Summary, Preface, Synopsis, Conclusion, Future Perspectives, or any section whose content depends on summarising, framing, or reflecting on the entire paper. Set False for all body sections that can be written independently.
# - build_order: the build execution order, globally sequential across all sections. Assign in this priority:
#   1. Firtst are All non-deferred sections first, numbered from 1 in logical narrative order.
#   2. Then the Deferred closing sections next (e.g. Conclusion, Future Perspectives) — these need the full body but not the opening sections.
#   3. And Finally the Deferred opening sections last (e.g. Abstract, Executive Summary) — these need the entire paper including closing sections, but each opening section is built independently.

# FORMATTING:
# - Use plain text for headings only.
# - NO markdown symbols (no #, *, or -).
# - NO numbering (no "Section 1" or "1.").
# - Each heading should be a standalone line."""),

#     ("user", """Topic: {topic}

# Description: {description}

# Generate the complete outline following the structural flow.""")
# ])

PLANNER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Research Architect. Your task is to design a comprehensive research paper outline that transforms technical points into a logical narrative.

UNIVERSAL STRUCTURAL FLOW:
Your outline must follow this logical progression:
1. THE FOUNDATION: Abstract and an Introduction that provides the "Hook" and significance of the topic.
2. THE MECHANISMS: Core theories, fundamental structures, or underlying principles.
3. THE CONTEXT: Comparative analysis, historical background, or benchmarking against standards.
4. THE CHALLENGE: Critical examination of problems, limitations, or existing gaps.
5. THE TECHNICAL ANALYSIS: Data-driven solutions, performance metrics, or specialized findings.
6. THE APPLICATION: Practical implementation, industrial constraints, or real-world scalability.
7. THE SYNTHESIS: Conclusion including summary of findings and Future Perspectives.

MANDATORY REQUIREMENTS:
1. Include ALL required headings: {compulsory_headings}
2. Try to Integrate ALL key points logically within the flow: {points_to_include}
3. Generate at least {min_sections} total sections. do not exceed 1.5 times the minimum requirements.

DESIGN PRINCIPLES:
- Use clear, specific, and descriptive phrases for headings.
- Ensure a "Story Arc" where each section builds upon the previous one.
- Maintain a balance between foundational theory and practical application.

SECTION METADATA RULES:
- position: reflects the final reading order of the paper. 
- is_deferred: Analyse each section heading semantically. Set True for any section that requires the full paper to be written before it can be generated — such as Abstract, Executive Summary, Preface, Synopsis, Conclusion, Future Perspectives, or any section whose content depends on summarising, framing, or reflecting on the entire paper. Set False for all body sections that can be written independently.
- build_order: the build execution order, globally sequential across all sections. Assign in this priority:
  1. Firtst are All non-deferred sections first, numbered from 1 in logical narrative order.
  2. Then the Deferred closing sections next (e.g. Conclusion, Future Perspectives) — these need the full body but not the opening sections.
  3. And Finally the Deferred opening sections last (e.g. Abstract, Executive Summary) — these need the entire paper including closing sections, but each opening section is built independently.
- section_type: "normal" or "deferred_opening" or "deferred_closing".

FORMATTING:
- Use plain text for headings only.
- NO markdown symbols (no #, *, or -).
- NO numbering (no "Section 1" or "1.").
- Each heading should be a standalone line."""),

    ("user", """Topic: {topic}

Description: {description}

Generate the complete outline following the structural flow.""")
])

from langchain_core.prompts import ChatPromptTemplate

BUILDER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Technical Research Writer composing one section of a multi-section academic paper.

CONTEXT:
- Topic: {topic}
- Current Section: {heading}
- Established Facts: {established_facts} (treat as given; extend, do not repeat)
- Narrative Position: {narrative_position}
- Open Threads: {open_threads}
- Next Section Direction: {next_section_expectation}

OBJECTIVE:
Advance the paper’s argument with technically rigorous analysis. Introduce new reasoning, models, mechanisms, or formal structure as appropriate.

CONSTRAINTS:
- Do NOT repeat established facts.
- Do NOT write a concluding summary.
- Do NOT resolve the full thesis unless this is explicitly a conclusion section.
- End by naturally preparing for: {next_section_expectation}.

FORMAT:
- Begin with: ## {heading}
- Use clear paragraphs and ### subheadings if helpful.
- Use **bold** for key terms.
- Use LaTeX for equations when needed.
- Academic tone. No filler.

LENGTH:
700–1000 words (or 400–800 if topic is general).

Write the section now."""),

    ("user", """Write the complete section for: {heading}""")
])

DEFERRED_OPENING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are writing an opening section of an academic paper.

CONTEXT:
- Topic: {topic}
- Section Title: {heading}
- Full Paper (in order): {completed_sections}

OBJECTIVE:
Write the requested opening section using full knowledge of the completed paper.

RULES:
- Use only material established in the paper.
- Do NOT introduce new claims, data, or arguments.
- Synthesize rather than repeat.
- Adapt to the function implied by {heading}
  (e.g., Abstract = concise synthesis; Introduction = framing and motivation; Executive Summary = high-level distillation).

FORMAT:
- Begin with: ## {heading}
- Academic tone.
- 400–700 words (shorter if Abstract).

Write the section now."""),
    
    ("user", "Write the complete section for: {heading}")
])

DEFERRED_CLOSING_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are writing a late-stage section of an academic paper.

CONTEXT:
- Topic: {topic}
- Section Title: {heading}
- Completed Sections (in order): {completed_sections}

OBJECTIVE:
Using only the completed sections, write the requested section.

RULES:
- Do NOT introduce new data, theories, or arguments.
- Build strictly from previously established material.
- Synthesize rather than repeat.
- Adapt to the function implied by {heading} 
  (e.g., Conclusion, Future Work, Limitations, Discussion, Implications).

BEHAVIOR:
- If the heading implies full conclusion → provide intellectual closure.
- If it implies future directions → extend from established results.
- If it implies limitations → critically evaluate prior arguments.
- If it implies discussion → integrate and reflect.

FORMAT:
- Begin with: ## {heading}
- Academic tone.
- 600–900 words.

Write the section now."""),
    
    ("user", "Write the complete section for: {heading}")
])

SECTION_SUMMARIZER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Research Analyst.

Your goal is NOT to record everything.
Your goal is to preserve only information required for narrative continuity.

Remove:
- Redundant explanation
- Supporting examples unless critical
- Minor statistics
- Restated claims

Keep:
- Core claims
- Critical data points
- Definitions that are reused later
- Explicit forward references

Output Format:

FIELD 1 — continuity_summary:
A concise but complete narrative-focused summary (200–350 words).

FIELD 2 — open_threads:
A list of unresolved questions, promises made to the reader, or topics explicitly flagged for future sections.
Each thread must be a single standalone sentence.
Return [] if none."""),

    ("user", """Summarize the following section for continuity purposes:

{section_content}""")
])

GLOBAL_SUMMARY_UPDATER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Research Continuity Manager. Your task is to update the global state tracker for an ongoing research paper after a new section has been written.

You will receive:
- The previous global summary (may be blank if this is the first section)
- The fact sheet of the newly completed section
- The full outline of the paper
- The heading of the section just completed

Your job is to rewrite the global summary with the following fields:

sections_covered:
Add the newly completed heading to the existing list. Preserve order.

established_facts:
Merge the previous established facts with the KEY ARGUMENTS and DATA & DEFINITIONS from the new fact sheet.
Compress and deduplicate — remove redundancy, keep only what is essential and locked in.
Format as dense structured bullets.

narrative_position:
Update using the NARRATIVE CONTRIBUTION from the new fact sheet.
Write 1-2 sentences describing where the paper currently stands in its story arc.

open_threads:
Review previous open threads and the new fact sheet's open threads.
Retire any threads that were resolved or addressed by the new section.
Carry forward all still-live threads.
Add any new threads from the new fact sheet.
Each thread must be a single standalone sentence.

next_section_expectation:
Look at the outline and identify the next non-deferred section to be built after the current one.
Write 2-3 sentences max on what that section must deliver — its angle, depth, and contribution to the paper.
If no non-deferred sections remain, write what the next deferred closing section should deliver."""),

    ("user", """PREVIOUS GLOBAL SUMMARY:
sections_covered: {prev_sections_covered}
established_facts: {prev_established_facts}
narrative_position: {prev_narrative_position}
open_threads: {prev_open_threads}
next_section_expectation: {prev_next_section_expectation}

NEW FACT SHEET:
{fact_sheet}

OUTLINE:
{outline}

SECTION JUST COMPLETED: {current_heading}

Update the global summary.""")
])
