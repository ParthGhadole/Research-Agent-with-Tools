# # # import asyncio
# # # from playwright.async_api import async_playwright

# # # async def get_page_content(url):
# # #     async with async_playwright() as p:
# # #         # Launch the browser asynchronously
# # #         browser = await p.chromium.launch(headless=True)
# # #         page = await browser.new_page()
        
# # #         # Navigate and wait for the page to load
# # #         await page.goto(url, wait_until="load")
        
# # #         # Get the page content
# # #         content = await page.content()
        
# # #         await browser.close()
# # #         return content

# # # # To call this from an async function:
# # # async def main():
# # #     url = "https://medium.com/@knish5790/roadmap-to-mastering-agentic-ai-bde9e0236997"
# # #     content = await get_page_content(url)
# # #     print(content)


# # # if __name__ == "__main__":
# # #     asyncio.run(main())

# # import asyncio
# # from playwright.async_api import async_playwright

# # async def get_page_content(url):
# #     async with async_playwright() as p:
# #         browser = await p.chromium.launch(headless=True)
# #         # Use a context with a realistic user agent
# #         context = await browser.new_context(
# #             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
# #         )
# #         page = await context.new_page()
        
# #         # Change wait_until to 'domcontentloaded' to avoid waiting for endless trackers
# #         await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
# #         content = await page.content()
# #         await browser.close()
# #         return content

# # async def main():
# #     url = "https://medium.com/@knish5790/roadmap-to-mastering-agentic-ai-bde9e0236997"
# #     content = await get_page_content(url)
# #     print("Successfully retrieved content length:", len(content))
# #     print(content)

# # if __name__ == "__main__":
# #     asyncio.run(main())

# import asyncio
# from playwright.async_api import async_playwright

# async def get_page_content(url):
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         context = await browser.new_context(
#             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#         )
#         page = await context.new_page()
        
#         await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
#         content = await page.content()
#         await browser.close()
#         return content

# async def main():
#     url = "https://medium.com/@knish5790/roadmap-to-mastering-agentic-ai-bde9e0236997"
#     content = await get_page_content(url)
    
#     # Save the content to a file
#     filename = "medium_page.html"
#     with open(filename, "w", encoding="utf-8") as f:
#         f.write(content)
        
#     print(f"Successfully retrieved content and saved to {filename}")

# if __name__ == "__main__":
#     asyncio.run(main())

# ### Below Works for url
# import asyncio
# import trafilatura
# from playwright.async_api import async_playwright

# async def get_clean_article(url):
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         # Using a context with a standard desktop user agent
#         context = await browser.new_context(
#             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#         )
#         page = await context.new_page()
        
#         # Navigate and wait for the main content to render
#         await page.goto(url, wait_until="networkidle", timeout=60000)
        
#         # Get the full HTML
#         html_content = await page.content()
#         await browser.close()
        
#         # Use trafilatura to extract clean text/markdown
#         # This removes headers, footers, sidebars, and scripts
#         text = trafilatura.extract(html_content, output_format='markdown', include_images=True)
#         return text

# async def test():
#     # url = "https://medium.com/@knish5790/roadmap-to-mastering-agentic-ai-bde9e0236997"
#     url = "https://www.academia.edu/download/59817925/IRJET-V6I217620190621-73452-h5pwu7.pdf"
#     print("Fetching article...")
    
#     clean_text = await get_clean_article(url)
    
#     if clean_text:
#         with open("clean_article.md", "w", encoding="utf-8") as f:
#             f.write(clean_text)
#         print("Success! Cleaned article saved to 'clean_article.md'")
#     else:
#         print("Failed to extract content. You may be blocked by a security challenge.")

# if __name__ == "__main__":
#     asyncio.run(test())


import asyncio
import requests
import trafilatura
import fitz  # PyMuPDF
from playwright.async_api import async_playwright
from io import BytesIO

async def scrape_html(url):
    """Scrapes standard web pages using Playwright and Trafilatura."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        # Use 'domcontentloaded' to avoid waiting for heavy tracking scripts
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        html_content = await page.content()
        await browser.close()
        return trafilatura.extract(html_content, output_format='markdown', include_images=True)

def scrape_pdf(url):
    """Downloads and extracts text from PDFs using PyMuPDF."""
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        return None
    
    # Open PDF from bytes
    doc = fitz.open(stream=BytesIO(response.content), filetype="pdf")
    text = "\n".join([page.get_text() for page in doc])
    return f"# PDF Content\n\n{text}"

async def get_best_content(url):
    print(f"Analyzing URL: {url}")
    
    # 1. Use a lightweight HEAD request to inspect the final URL and Content-Type
    try:
        response = requests.head(url, allow_redirects=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        content_type = response.headers.get('Content-Type', '').lower()
        final_url = response.url
    except:
        content_type = ""
        final_url = url

    # 2. Logic based on real content, not just extension
    if "pdf" in content_type or final_url.lower().endswith(".pdf"):
        print(f"Detected PDF content at: {final_url}")
        return scrape_pdf(final_url)
    else:
        print(f"Detected HTML content. Using Playwright on: {final_url}")
        return await scrape_html(final_url)

async def main():
    urls = [
        # "https://medium.com/@knish5790/roadmap-to-mastering-agentic-ai-bde9e0236997",
        # "https://www.academia.edu/download/59817925/IRJET-V6I217620190621-73452-h5pwu7.pdf",
        "https://www.princexml.com/samples/invoice-plain/index.pdf"
    ]
    
    for url in urls:
        content = await get_best_content(url)
        if content:
            filename = f"extracted_{urls.index(url)}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Success! Saved to {filename}")
        else:
            print(f"Failed to extract from {url}")

if __name__ == "__main__":
    asyncio.run(main())