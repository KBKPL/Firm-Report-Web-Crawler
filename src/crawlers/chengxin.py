import os
import logging
import json
import html
from typing import List, Dict, Optional, Tuple

from bs4 import BeautifulSoup
from docx import Document

from src.crawlers.base import CompanyCrawler
from src.utils.http_utils import session
from src.utils.pdf_utils import extract_text_from_pdf
from src.utils.text_utils import sanitize_text, find_paragraphs_with_keyword
from src.utils.docx_utils import add_keyword_paragraphs, save_crawler_docx

logger = logging.getLogger(__name__)

class ChengxinCrawler(CompanyCrawler):
    SECTIONS = {
        "1": ("业绩报告", "quarterly performance", "crawl_quarterly_performance"),
        "2": ("公司公告", "company announcements", "crawl_company_announcements"),
    }

    def __init__(self, full_code: str, config: dict):
        super().__init__(full_code, config)
        self.page_size = config.get("page_size", 10)
        self.quarterly_url = config.get("quarterly_url")

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
            url = self.quarterly_url.format(page=page_index * self.page_size)
            resp = session.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            items = soup.find_all("div", class_="cbox-2 p_loopitem")
            if not items:
                break
            break_page = False
            for item in items:
                title = item.find("h1", class_="e_h1-4 s_subtitle").get_text(strip=True)
                pub_date = item.find("p", class_="e_timeFormat-18 s_title").get_text(strip=True)
                if end_date and pub_date > end_date:
                    continue
                if start_date and pub_date < start_date:
                    break_page = True
                    break
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
                text = extract_text_from_pdf(pdf_url)
                text = sanitize_text(text)
                for kw in keywords:
                    paras = find_paragraphs_with_keyword(text, kw)
                    if not paras:
                        continue
                    doc = docs[kw]
                    doc.add_heading(f"{pub_date}_{title}", level=1)
                    add_keyword_paragraphs(doc, paras, kw, pdf_url)
            if break_page or len(items) < self.page_size:
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
            logger.info(f"Fetching page: {page_index}")
            url = self.quarterly_url.format(page=page_index * self.page_size)
            resp = session.get(url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            items = soup.find_all("div", class_="cbox-2 p_loopitem")
            if not items:
                break
            break_page = False
            for item in items:
                title = item.find("h1", class_="e_h1-4 s_subtitle").get_text(strip=True)
                pub_date = item.find("p", class_="e_timeFormat-18 s_title").get_text(strip=True)
                if end_date and pub_date > end_date:
                    continue
                if start_date and pub_date < start_date:
                    break_page = True
                    break
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
                text = extract_text_from_pdf(pdf_url)
                text = sanitize_text(text)
                for kw in keywords:
                    paras = find_paragraphs_with_keyword(text, kw)
                    if not paras:
                        continue
                    doc = docs[kw]
                    doc.add_heading(f"{pub_date}_{title}", level=1)
                    add_keyword_paragraphs(doc, paras, kw, pdf_url)
            if break_page or len(items) < self.page_size:
                break
            page_index += 1
        section_label = self.SECTIONS["1"][0]
        for kw, doc in docs.items():
            path = save_crawler_docx(doc, self.full_code, kw, section_label, output_dir)
            generated[kw] = path
        return generated
