import os
import logging
import json
import html
from typing import List, Dict, Optional, Tuple
import urllib.parse
import tempfile
import subprocess

from bs4 import BeautifulSoup
from docx import Document

from src.crawlers.base import CompanyCrawler
from src.utils.http_utils import session
from src.utils.text_utils import sanitize_text, find_paragraphs_with_keyword
from src.utils.docx_utils import add_keyword_paragraphs, save_crawler_docx

logger = logging.getLogger(__name__)

class ChengxinCrawler(CompanyCrawler):
    SECTIONS = {
        "1": ("业绩报告", "quarterly performance", "crawl_quarterly_performance"),
        "2": ("ESG报告", "company announcements", "crawl_company_announcements"),
    }

    def __init__(self, full_code: str, config: dict):
        super().__init__(full_code, config)
        self.page_size = config.get("page_size", 10)
        self.quarterly_url = config.get("quarterly_url")
        self.announcement_url = config.get("company_announcement_url")

    def _download_chengxin_pdf(self, url: str) -> bytes:
        """Download PDF with encoding and referer header for Chengxin site."""
        encoded = urllib.parse.quote(url, safe=':/?&=%')
        resp = session.get(encoded, timeout=10, headers={'Referer': 'https://www.cxlithium.com/'})
        resp.raise_for_status()
        return resp.content

    def _extract_text_from_chengxin_pdf(self, pdf_url: str) -> str:
        """Download PDF via Chengxin-specific downloader and extract text."""
        pdf_bytes = self._download_chengxin_pdf(pdf_url)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
            tmp_pdf.write(pdf_bytes)
            tmp_pdf_path = tmp_pdf.name
        tmp_txt = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        tmp_txt.close()
        try:
            subprocess.run(['pdftext', tmp_pdf_path, '--out_path', tmp_txt.name], check=True)
            with open(tmp_txt.name, 'r', encoding='utf-8') as f:
                text = f.read()
            return text
        finally:
            if os.path.exists(tmp_pdf_path):
                os.remove(tmp_pdf_path)
            if os.path.exists(tmp_txt.name):
                os.remove(tmp_txt.name)

    def fetch_quarterly_performance_page(self, page_index: int) -> List[Dict[str, str]]:
        """Fetch one page of quarterly performance metadata."""
        # build URL for page
        url = self.quarterly_url.format(page=(page_index * self.page_size))
        logger.info(f"Fetching page: {url}")
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        items = soup.find_all("div", class_="cbox-2 p_loopitem")
        records: List[Dict[str, str]] = []
        for item in items:
            title = item.find("h1", class_="e_h1-4 s_subtitle").get_text(strip=True)
            pub_date = item.find("p", class_="e_timeFormat-18 s_title").get_text(strip=True)
            input_tag = item.find("input", attrs={"name": "fileList"})
            if not input_tag or not input_tag.get("value"):
                logger.warning(f"No fileList JSON for {title}")
                continue
            raw = input_tag["value"]
            unesc = html.unescape(raw)
            try:
                files = json.loads(unesc)
                file_info = files[0]
                pdf_url = file_info.get("fileUrl")
            except Exception as e:
                logger.error(f"Failed parsing fileList for {title}: {e}")
                continue
            records.append({"title": title, "publishDate": pub_date, "pdf_url": pdf_url})
        return records

    def fetch_company_announcements_page(self, page_index: int) -> List[Dict[str, str]]:
        """Fetch one page of company announcements metadata."""
        if page_index == 0:
            url = "https://www.cxlithium.com/companyfile/6/"
        else:
            url = self.announcement_url.format(page=(page_index * self.page_size))
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        items = soup.find_all("div", class_="cbox-2 p_loopitem")
        records: List[Dict[str, str]] = []
        for item in items:
            title = item.find("h1", class_="e_h1-4 s_subtitle").get_text(strip=True)
            pub_date = item.find("p", class_="e_timeFormat-18 s_title").get_text(strip=True)
            input_tag = item.find("input", attrs={"name": "fileList"})
            if not input_tag or not input_tag.get("value"):
                logger.warning(f"No fileList JSON for {title}")
                continue
            raw = input_tag["value"]
            unesc = html.unescape(raw)
            try:
                files = json.loads(unesc)
                file_info = files[0]
                pdf_url = file_info.get("fileUrl")
            except Exception as e:
                logger.error(f"Failed parsing fileList for {title}: {e}")
                continue
            records.append({"title": title, "publishDate": pub_date, "pdf_url": pdf_url})
        return records

    def crawl_quarterly_performance(
        self,
        keywords: List[str],
        output_dir: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        docs = {kw: Document() for kw in keywords}
        generated: Dict[str, str] = {}
        page_index = 0
        while True:
            logger.info(f"Fetching page: {page_index}")
            records = self.fetch_quarterly_performance_page(page_index)
            if not records:
                break
            break_page = False
            for rec in records:
                title = rec.get("title", "")
                pub_date = rec.get("publishDate", "")
                if end_date and pub_date > end_date:
                    continue
                if start_date and pub_date < start_date:
                    break_page = True
                    break
                pdf_url = rec.get("pdf_url")
                text = self._extract_text_from_chengxin_pdf(pdf_url)
                text = sanitize_text(text)
                for kw in keywords:
                    paras = find_paragraphs_with_keyword(text, kw)
                    if not paras:
                        continue
                    doc = docs[kw]
                    doc.add_heading(f"{pub_date}_{title}", level=1)
                    add_keyword_paragraphs(doc, paras, kw, pdf_url)
            if break_page or len(records) < self.page_size:
                break
            page_index += 1
        section_label = self.SECTIONS["1"][0]
        for kw, doc in docs.items():
            path = save_crawler_docx(doc, self.full_code, kw, section_label, output_dir)
            generated[kw] = path
        return generated

    def crawl_company_announcements(
        self,
        keywords: List[str],
        output_dir: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        docs = {kw: Document() for kw in keywords}
        generated: Dict[str, str] = {}
        page_index = 0
        while True:
            logger.info(f"Fetching announcements page: {page_index}")
            records = self.fetch_company_announcements_page(page_index)
            if not records:
                break
            break_page = False
            for rec in records:
                title = rec.get("title", "")
                pub_date = rec.get("publishDate", "")
                if end_date and pub_date > end_date:
                    continue
                if start_date and pub_date < start_date:
                    break_page = True
                    break
                pdf_url = rec.get("pdf_url")
                text = self._extract_text_from_chengxin_pdf(pdf_url)
                text = sanitize_text(text)
                for kw in keywords:
                    paras = find_paragraphs_with_keyword(text, kw)
                    if not paras:
                        continue
                    doc = docs[kw]
                    doc.add_heading(f"{pub_date}_{title}", level=1)
                    add_keyword_paragraphs(doc, paras, kw, pdf_url)
            if break_page or len(records) < self.page_size:
                break
            page_index += 1
        section_label = self.SECTIONS["2"][0]
        for kw, doc in docs.items():
            path = save_crawler_docx(doc, self.full_code, kw, section_label, output_dir)
            generated[kw] = path
        return generated
