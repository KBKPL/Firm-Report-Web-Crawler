"""
Main module for PDF keyword search and exporting matching paragraphs to a docx file.
"""

import logging
import sys
import subprocess
from bs4 import BeautifulSoup
import urllib.parse

from http_utils import session
from pdf_utils import download_pdf
from text_utils import find_paragraphs_with_keyword
from docx_utils import write_paragraphs_to_docx

def main():
    # Interactive mode
    url = input("Please enter the URL: ").strip()
    if not url:
        print("No URL entered. Exiting.")
        sys.exit(0)
    # Fetch content once
    print(f"Fetching URL {url}...")
    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        logging.error(f"Error fetching URL: {e}")
        sys.exit(1)
    ctype = resp.headers.get("content-type", "").lower()
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    # Extract text
    if "html" in ctype and "url" not in qs:
        # Render JS pages
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("Playwright not installed. Run 'pip install playwright' and 'playwright install'.")
            sys.exit(1)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")
            html_text = page.content()
            browser.close()
        text = BeautifulSoup(html_text, "lxml").get_text("\n")
    else:
        # PDF handling
        pdf_bytes = download_pdf(url)
        sample_pdf = "sample.pdf"
        with open(sample_pdf, "wb") as f:
            f.write(pdf_bytes)
        print("Converting PDF to text via pdftext CLI...")
        try:
            subprocess.run(["pdftext", sample_pdf, "--out_path", "converted.txt"], check=True)
        except Exception as e:
            logging.error(f"Error converting PDF to text: {e}")
            sys.exit(1)
        with open("converted.txt", "r", encoding="utf-8") as f:
            text = f.read()
    # Collect multiple keywords
    print("Enter keywords one by one. Press Enter on an empty prompt to finish.")
    keywords = []
    idx = 1
    while True:
        kw = input(f"Please enter keyword {idx}: ").strip()
        if not kw:
            break
        keywords.append(kw)
        idx += 1
    if not keywords:
        print("No keywords entered. Exiting.")
        sys.exit(0)
    # Process each keyword
    for kw in keywords:
        print(f"Searching for '{kw}'...")
        paragraphs = find_paragraphs_with_keyword(text, kw)
        if not paragraphs:
            print(f"No paragraphs found for '{kw}'.")
            continue
        safe_kw = kw.replace(" ", "_")
        output_file = f"result_{safe_kw}.docx"
        print(f"Writing {len(paragraphs)} paragraphs to {output_file}...")
        write_paragraphs_to_docx(paragraphs, output_file, kw)
        print(f"Done for '{kw}'.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Interrupted by user. Exiting.")
        sys.exit(0)