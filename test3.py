import asyncio
import requests
import trafilatura
import fitz
from io import BytesIO
from playwright.async_api import async_playwright
from playwright_stealth import Stealth  # Updated import

async def scrape_html(url):
    """Scrapes standard web pages with stealth to bypass Cloudflare."""
    # Wrap the entire playwright lifecycle in the Stealth handler
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        
        # Extract HTML
        html_content = await page.content()
        main_text = trafilatura.extract(html_content, output_format='markdown')
        
        # Look for PDF embeds
        pdf_src = await page.evaluate('''() => {
            const el = document.querySelector('iframe, embed, object');
            return el ? (el.src || el.data) : null;
        }''')
        
        await browser.close()
        
        if pdf_src and pdf_src.lower().endswith('.pdf'):
            from urllib.parse import urljoin
            pdf_url = urljoin(url, pdf_src)
            print(f"Found embedded PDF: {pdf_url}")
            pdf_text = scrape_pdf(pdf_url)
            return f"{main_text}\n\n# PDF Content\n{pdf_text}"
        
        return main_text

def scrape_pdf(url):
    """Downloads and extracts text from PDFs using PyMuPDF."""
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if response.status_code == 200:
            doc = fitz.open(stream=BytesIO(response.content), filetype="pdf")
            return "\n".join([page.get_text() for page in doc])
    except Exception as e:
        print(f"PDF extraction error: {e}")
    return None

async def get_best_content(url):
    print(f"Analyzing URL: {url}")
    try:
        response = requests.head(url, allow_redirects=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        content_type = response.headers.get('Content-Type', '').lower()
        final_url = response.url
    except:
        content_type = ""
        final_url = url

    if "pdf" in content_type or final_url.lower().endswith(".pdf"):
        return scrape_pdf(final_url)
    else:
        return await scrape_html(final_url)

async def main():
    urls = [
        # "https://medium.com/@knish5790/roadmap-to-mastering-agentic-ai-bde9e0236997",
        # "https://www.academia.edu/download/59817925/IRJET-V6I217620190621-73452-h5pwu7.pdf",
        "https://www.princexml.com/samples/textbook/somatosensory.pdf"
    ]
    
    for i, url in enumerate(urls):
        content = await get_best_content(url)
        if content:
            filename = f"extracted_{i}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Success! Saved to {filename}")

if __name__ == "__main__":
    asyncio.run(main())