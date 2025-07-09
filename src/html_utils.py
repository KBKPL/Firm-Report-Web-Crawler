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
