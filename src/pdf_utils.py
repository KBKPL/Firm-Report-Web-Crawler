"""
PDF utilities: download PDFs (including preview URL decoding).
"""
import sys
import logging
import urllib.parse
import base64
from http_utils import session

logger = logging.getLogger(__name__)

def download_pdf(url: str) -> bytes:
    """Download a PDF from a URL. Handles Base64-encoded preview queries."""
    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        ctype = resp.headers.get('content-type', '').lower()
        if 'html' in ctype:
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            b64 = qs.get('url', [None])[0]
            if b64:
                real_url = base64.urlsafe_b64decode(b64).decode()
                resp = session.get(real_url, timeout=10)
                resp.raise_for_status()
                return resp.content
            logger.error("HTML response but no 'url' parameter for PDF preview.")
            sys.exit(1)
        return resp.content
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        sys.exit(1)
