"""
Crawler for Sinomine (company code sz002738) reports.
Fetches report metadata via JSON API and downloads each PDF for keyword extraction.
"""
import os
import logging
import subprocess
import base64
import re
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

from http_utils import session
from pdf_utils import download_pdf
from text_utils import find_paragraphs_with_keyword
from html_utils import find_paragraphs_from_html
from docx_utils import write_paragraphs_to_docx
from bs4 import BeautifulSoup  # for extracting full page text

API_LIST_URL = "https://server.comein.cn/comein/irmcenter/anonymous/irstore/report/list"
PAGE_SIZE = 10

# Base URL for HTML detail pages and default store ID for Sinomine
DETAIL_BASE_URL = "https://irm-enterprise-pc.comein.cn/investors/flow/report/detail"
STORE_ID = "21113"

def fetch_rendered_html(url: str) -> str:
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

def save_page_as_pdf(url: str, output_path: str) -> bool:
    """Render a page and save it as PDF using Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logging.error("Playwright not installed. Run 'pip install playwright' and 'playwright install'.")
        return False
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000, wait_until="networkidle")
            page.pdf(path=output_path, format="A4", print_background=True)
            browser.close()
        return True
    except Exception as e:
        logging.error(f"Error saving PDF via Playwright: {e}")
        return False

def fetch_report_page(full_code: str, page_index: int = 0, page_num: int = PAGE_SIZE) -> list[dict]:
    """Fetch one page of report metadata using 0-based page index (pagestart)."""
    payload = {
        "pagestart": page_index,  # page number (0-based)
        "pagenum": page_num,
        "fullCode": full_code,
        "keyword": "",
        "languageType": 0
    }
    try:
        resp = session.post(API_LIST_URL, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "0":
            logging.error(f"List API error: {data}")
            return []
        return data.get("rows", [])
    except Exception as e:
        logging.error(f"Error fetching report list: {e}")
        return []


def crawl_company(full_code: str, keywords: list[str], output_dir: str = "results", start_date: str = None):
    """Crawl all reports for given company and extract paragraphs for each keyword."""
    os.makedirs(output_dir, exist_ok=True)
    # filter records published before start_date (YYYY-MM-DD)
    # start_date None means no filter
    page_index = 0  # 0-based page number for pagination
    while True:
        logging.info(f"Fetching page: {page_index}")
        records = fetch_report_page(full_code, page_index, PAGE_SIZE)
        if not records:
            break
        for rec in records:
            # skip records before start_date
            pub_date = rec.get("publishDate", "").split()[0]
            if start_date and pub_date and pub_date < start_date:
                logging.info(f"Skipping record {rec.get('id')} published on {pub_date}")
                continue
            rec_id = rec.get('id')
            raw_url = rec.get('url')
            logging.info(raw_url)
            if not raw_url:
                report_id = rec.get('reportId') or rec_id
                detail_url = f"{DETAIL_BASE_URL}?id={report_id}&type={rec.get('type')}&storeId={STORE_ID}"
                logging.info(f"Rendering HTML for record {rec_id} from: {detail_url}")
                html_text = fetch_rendered_html(detail_url)
                if not html_text:
                    continue
                # save webpage as PDF
                safe_title = re.sub(r'\W+', '_', rec.get('title','')).strip('_')
                safe_author = re.sub(r'\W+', '_', rec.get('author','')).strip('_')
                pdf_dir = 'original files'
                os.makedirs(pdf_dir, exist_ok=True)
                pdf_name = f"{full_code}_{safe_title}_{safe_author}.pdf"
                pdf_path = os.path.join(pdf_dir, pdf_name)
                save_page_as_pdf(detail_url, pdf_path)
                logging.info(f"Saved PDF {pdf_name}")
                # search in HTML
                page_text = BeautifulSoup(html_text, "lxml").get_text("\n")
                for kw in keywords:
                    paras = find_paragraphs_with_keyword(page_text, kw)
                    if not paras:
                        continue
                    safe_title = re.sub(r'\W+', '_', rec.get('title', '')).strip('_')
                    date = rec.get('publishDate', '').split()[0]
                    safe_kw = kw.replace(' ', '_')
                    out_file = f"{full_code}_{safe_title}_{safe_kw}_{date}.docx"
                    out_path = os.path.join(output_dir, out_file)
                    write_paragraphs_to_docx(paras, out_path, kw)
                continue
            # HTML detail page handling
            if '/report/detail' in raw_url:
                logging.info(f"Rendering HTML for record {rec_id} from: {raw_url}")
                html_text = fetch_rendered_html(raw_url)
                if not html_text:
                    continue
                # extract full text and search paragraphs
                page_text = BeautifulSoup(html_text, "lxml").get_text("\n")
                for kw in keywords:
                    paras = find_paragraphs_with_keyword(page_text, kw)
                    if not paras:
                        continue
                    safe_title = re.sub(r'\W+', '_', rec.get('title', '')).strip('_')
                    date = rec.get('publishDate', '').split()[0]
                    safe_kw = kw.replace(' ', '_')
                    out_file = f"{full_code}_{safe_title}_{safe_kw}_{date}.docx"
                    out_path = os.path.join(output_dir, out_file)
                    write_paragraphs_to_docx(paras, out_path, kw)
                continue
            # PDF handling
            # always use file-view preview to fetch PDF bytes
            if 'onlinePreview' in raw_url:
                preview_url = raw_url
            else:
                b64 = base64.urlsafe_b64encode(raw_url.encode()).decode()
                preview_url = (
                    f"https://file-view.comein.cn/onlinePreview?url={b64}"
                    "&officePreviewSwitchDisabled=true"
                    "&officePreviewType=pdf"
                    "&watermarkTxt="
                )
            logging.info(f"Downloading PDF for record {rec_id} from: {preview_url}")
            pdf_bytes = download_pdf(preview_url)
            # detect HTML vs PDF content
            is_html = pdf_bytes.lstrip().startswith(b'<')
            if is_html:
                # HTML content
                text = pdf_bytes.decode('utf-8', errors='ignore')
            else:
                # write temp pdf and convert to text
                with open("temp.pdf", "wb") as f_pdf:
                    f_pdf.write(pdf_bytes)
                try:
                    subprocess.run(["pdftext", "temp.pdf", "--out_path", "temp.txt"], check=True)
                    with open("temp.txt", "r", encoding="utf-8") as f_txt:
                        text = f_txt.read()
                except Exception as e:
                    logging.error(f"Failed pdf->text for {preview_url}: {e}")
                    continue
            # search keywords and write docx
            for kw in keywords:
                paras = find_paragraphs_with_keyword(text, kw)
                if not paras:
                    continue
                title = rec.get("title", "")
                logging.info(f"Found for title {title}")
                # sanitize title for filename
                safe_title = re.sub(r'\W+', '_', title).strip('_')
                # prepare DOCX filename: code_title_keyword_publishdate
                date = rec.get("publishDate", "").split()[0]
                safe_kw = kw.replace(" ", "_")
                out_file = f"{full_code}_{safe_title}_{safe_kw}_{date}.docx"
                out_path = os.path.join(output_dir, out_file)
                write_paragraphs_to_docx(paras, out_path, kw)
                # save original file for keyword hit
                orig_dir = "original files"
                os.makedirs(orig_dir, exist_ok=True)
                author = rec.get("author", "")
                safe_author = re.sub(r'\W+', '_', author).strip('_')
                ext = ".html" if is_html else ".pdf"
                orig_fname = f"{full_code}_{safe_title}_{safe_author}{ext}"
                orig_path = os.path.join(orig_dir, orig_fname)
                with open(orig_path, "wb") as f:
                    f.write(pdf_bytes)
                logging.info(f"Saved original file {orig_fname}")
        if len(records) < PAGE_SIZE:
            break
        page_index += 1


def download_original_reports(full_code: str, start_date: str = '2025-01-01', output_dir: str = 'original files'):
    """Download all PDFs from reports published after start_date."""
    os.makedirs(output_dir, exist_ok=True)
    page_index = 0  # 0-based page number for pagination
    while True:
        logging.info(f"Fetching page (original files): {page_index}")
        records = fetch_report_page(full_code, page_index, PAGE_SIZE)
        if not records:
            break
        for rec in records:
            pub_date = rec.get('publishDate', '').split()[0]
            logging.info(pub_date)
            if not pub_date or pub_date < start_date:
                continue
            raw_url = rec.get('url')
            logging.info(raw_url)
            if not raw_url:
                report_id = rec.get('reportId') or rec.get('id')
                detail_url = f"{DETAIL_BASE_URL}?id={report_id}&type={rec.get('type')}&storeId={STORE_ID}"
                logging.info(f"Downloading original HTML for record {rec.get('id')} from: {detail_url}")
                try:
                    resp = session.get(detail_url, timeout=10)
                    resp.raise_for_status()
                    content = resp.content
                except Exception as e:
                    logging.error(f"Error downloading HTML: {e}")
                    continue
                ext = '.html'
            else:
                # Detect HTML detail pages
                if '/report/detail' in raw_url:
                    html_url = raw_url
                    logging.info(f"Downloading original HTML for record {rec.get('id')} from: {html_url}")
                    try:
                        resp = session.get(html_url, timeout=10)
                        resp.raise_for_status()
                        content = resp.content
                    except Exception as e:
                        logging.error(f"Error downloading HTML: {e}")
                        continue
                    ext = '.html'
                else:
                    # PDF via preview wrapper
                    if "onlinePreview" in raw_url:
                        preview_url = raw_url
                    else:
                        b64 = base64.urlsafe_b64encode(raw_url.encode()).decode()
                        preview_url = (
                            f"https://file-view.comein.cn/onlinePreview?url={b64}"
                            "&officePreviewSwitchDisabled=true"
                            "&officePreviewType=pdf"
                            "&watermarkTxt="
                        )
                    logging.info(f"Downloading original PDF for record {rec.get('id')} from: {preview_url}")
                    content = download_pdf(preview_url)
                    ext = '.pdf'
            # save original file with code_title_author
            title = rec.get('title', '')
            safe_title = re.sub(r'\W+', '_', title).strip('_')
            author = rec.get('author', '')
            safe_author = re.sub(r'\W+', '_', author).strip('_')
            orig_fname = f"{full_code}_{safe_title}_{safe_author}{ext}"
            orig_path = os.path.join(output_dir, orig_fname)
            try:
                with open(orig_path, 'wb') as f:
                    f.write(content)
                logging.info(f"Saved original file {orig_fname}")
            except Exception as e:
                logging.error(f"Failed to save original file: {e}")
        if len(records) < PAGE_SIZE:
            break
        page_index += 1


if __name__ == '__main__':
    # Download original files from April 1, 2025
    download_original_reports('sz002738')
