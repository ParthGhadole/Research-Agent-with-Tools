from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from langchain_core.tools import tool
import asyncio
import concurrent.futures

async def _run_crawl(url: str) -> dict:
    md_generator = DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.4)
    )
    config = CrawlerRunConfig(
        css_selector="main, article",
        excluded_tags=["nav", "footer", "script", "style", "aside"],
        word_count_threshold=5,
        markdown_generator=md_generator
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
    return {
        "url": url,
        "url_content": result.markdown
    }

def _crawl_in_new_loop(url: str) -> dict:
    """Spawns a fresh event loop in this thread — required on Windows where
    Playwright can't create subprocesses inside an already-running loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_run_crawl(url))
    finally:
        loop.close()

@tool
async def web_crawl_tool(url: str) -> dict:
    """
    Triggers content retrieval for a URL.
    Args:
        url (str): The link to be fetched.
    Returns:
        dict: A dict containing 'url' and 'url_content'.
    """
    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        result = await loop.run_in_executor(pool, _crawl_in_new_loop, url)
    return result