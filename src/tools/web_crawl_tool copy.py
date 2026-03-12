from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from langchain_core.tools import tool
@tool
async def web_crawl_tool(url: str) -> dict:
    """
    Triggers content retrieval for a URL.
    Args:
        url (str): The link to be fetched.
    Returns:
        dict: A dict containing 'url' and 'url_content'.
    """
    # content = await smart_web_scraper(url)
    # return {
    #     "url": url,
    #     "url_content": content
    # }
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


#new
import asyncio
import requests
import trafilatura
import fitz
from io import BytesIO
from playwright.async_api import async_playwright
from langchain_core.tools import tool

# --- Support Functions ---

async def _scrape_html(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        html_content = await page.content()
        await browser.close()
        return trafilatura.extract(html_content, output_format='markdown', include_images=True)

def _scrape_pdf(url):
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        return "Error: Could not download PDF."
    doc = fitz.open(stream=BytesIO(response.content), filetype="pdf")
    text = "\n".join([page.get_text() for page in doc])
    return f"# PDF Content\n\n{text}"

async def smart_web_scraper(url: str) -> str:
    """
    Analyzes a URL to detect if it is a PDF or HTML page, 
    then extracts and returns the content in Markdown format.
    """
    # Use synchronous HEAD request for initial inspection
    # Note: For fully async, consider using httpx.head instead of requests
    try:
        response = requests.head(url, allow_redirects=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        content_type = response.headers.get('Content-Type', '').lower()
        final_url = response.url
    except Exception as e:
        return f"Error connecting to URL: {str(e)}"

    # Determine type and scrape
    if "pdf" in content_type or final_url.lower().endswith(".pdf"):
        # Since _scrape_pdf is synchronous, it is safe to call here
        return _scrape_pdf(final_url)
    else:
        # Await the async scraper directly
        return await _scrape_html(final_url)