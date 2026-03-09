from src.util.models import GlobalSummary


def format_global_summary_for_prompt(global_summary: GlobalSummary) -> dict:
    """Formats GlobalSummary fields for prompt injection, replacing blank fields with readable placeholders."""

    sections_covered = (
        "\n".join(f"- {s}" for s in global_summary.sections_covered)
        if global_summary.sections_covered
        else "No sections written yet. This is the opening section."
    )

    established_facts = (
        global_summary.established_facts
        if global_summary.established_facts
        else "No facts established yet. Introduce foundational concepts freely."
    )

    narrative_position = (
        global_summary.narrative_position
        if global_summary.narrative_position
        else "This is the beginning of the paper. No narrative arc established yet."
    )

    open_threads = (
        "\n".join(f"- {t}" for t in global_summary.open_threads)
        if global_summary.open_threads
        else "No open threads yet."
    )

    next_section_expectation = (
        global_summary.next_section_expectation
        if global_summary.next_section_expectation
        else "Set the foundation. Introduce the topic, its significance, and core framing."
    )

    return {
        "sections_covered": sections_covered,
        "established_facts": established_facts,
        "narrative_position": narrative_position,
        "open_threads": open_threads,
        "next_section_expectation": next_section_expectation,
    }