
import asyncio
import requests
import trafilatura
import fitz  # PyMuPDF
from playwright.async_api import async_playwright
from io import BytesIO

async def scrape_html(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0...")
        page = await context.new_page()
        
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # 1. Get main page text
        html_content = await page.content()
        main_text = trafilatura.extract(html_content, output_format='markdown')
        
        # 2. Look for embedded PDFs (iframes, embeds, objects)
        embedded_pdf_url = await page.evaluate('''() => {
            const targets = document.querySelectorAll('iframe, embed, object');
            for (let el of targets) {
                const src = el.src || el.data;
                if (src && src.toLowerCase().endsWith('.pdf')) return src;
            }
            return null;
        }''')
        
        await browser.close()
        
        # 3. Combine: If PDF is found, fetch it; otherwise return just HTML
        if embedded_pdf_url:
            # Handle relative URLs (e.g., /download/file.pdf)
            if embedded_pdf_url.startswith('/'):
                from urllib.parse import urljoin
                embedded_pdf_url = urljoin(url, embedded_pdf_url)
            
            print(f"  -> Found embedded PDF: {embedded_pdf_url}")
            pdf_text = scrape_pdf(embedded_pdf_url)
            return f"{main_text}\n\n# Embedded PDF Content\n\n{pdf_text}"
            
        return main_text

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
        "https://medium.com/@knish5790/roadmap-to-mastering-agentic-ai-bde9e0236997",
        "https://www.academia.edu/download/59817925/IRJET-V6I217620190621-73452-h5pwu7.pdf"
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