"""
PDF utilities: download PDFs (including preview URL decoding).
"""
import sys
import logging
import urllib.parse
import base64
from src.utils.http_utils import session
import subprocess
import tempfile
import os

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

def extract_text_from_pdf(pdf_url: str) -> str:
    """Download a PDF from URL and extract its text using the pdftext CLI."""
    pdf_bytes = download_pdf(pdf_url)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        tmp_pdf.write(pdf_bytes)
        tmp_pdf_path = tmp_pdf.name
    tmp_txt = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    tmp_txt.close()
    try:
        subprocess.run(["pdftext", tmp_pdf_path, "--out_path", tmp_txt.name], check=True)
        with open(tmp_txt.name, "r", encoding="utf-8") as f:
            text = f.read()
        return text
    except Exception:
        raise
    finally:
        if os.path.exists(tmp_pdf_path):
            os.remove(tmp_pdf_path)
        if os.path.exists(tmp_txt.name):
            os.remove(tmp_txt.name)
