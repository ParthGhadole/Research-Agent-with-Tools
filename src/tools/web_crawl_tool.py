from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from langchain_core.tools import tool
@tool
async def web_crawl_tool(url: str) -> str:
    """
    Triggers content retrieval for a URL.
    Args:
        url (str): The link to be fetched.
    Returns:
        dict: A dict containing 'url' and 'url_content'.
    """
    url_to_crawl = url
    md_generator = DefaultMarkdownGenerator(
    content_filter=PruningContentFilter(threshold=0.4) # Adjust 0.3-0.6 for aggression
    )

    config = CrawlerRunConfig(
        css_selector="main, article",     # Only extract from these containers
        excluded_tags=["nav", "footer", "script", "style", "aside"],
        word_count_threshold=5,          # Removes tiny, irrelevant fragments
        markdown_generator=md_generator
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url_to_crawl,
            config=config
        )

    return {
        "url": url,
        "url_content": result.markdown
    }