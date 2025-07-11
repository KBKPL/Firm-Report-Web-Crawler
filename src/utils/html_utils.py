"""
HTML utilities: extract paragraphs from HTML content.
"""
import sys
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def find_paragraphs_from_html(html_text: str, keyword: str) -> list[str]:
    """Extract <p> tag paragraphs containing the keyword."""
    try:
        soup = BeautifulSoup(html_text, "lxml")
    except Exception as e:
        logger.error(f"Error parsing HTML: {e}")
        sys.exit(1)
    keyword_lower = keyword.lower()
    paras = [p.get_text(strip=True) for p in soup.find_all('p') if p.get_text(strip=True)]
    return [p for p in paras if keyword_lower in p.lower()]

def fetch_rendered_html(url: str) -> str | None:
    """Use Playwright to render JS-driven pages and return full HTML."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logging.error("Playwright not installed. Run 'pip install playwright' and 'playwright install'.")
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")
            html = page.content()
            browser.close()
        return html
    except Exception as e:
        logging.error(f"Error rendering HTML via Playwright: {e}")
        return None
