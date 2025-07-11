"""
Main module for PDF keyword search and exporting matching paragraphs to a docx file.
"""

import logging
import sys
import os
from pathlib import Path
from src.config import load_config, get_company_config
from src.crawlers.sinomine import SinomineCrawler
from src.crawlers.ganfeng import GanfengCrawler

# Project root one level above src
BASE_DIR = Path(__file__).parent.parent

CRAWLER_MAP = {
    "sinomine": SinomineCrawler,
    'ganfeng': GanfengCrawler,
}

def main():
    # select company
    config_all = load_config()
    companies = list(config_all.keys())
    print("Select company:")
    for idx, name in enumerate(companies, start=1):
        print(f"{idx}. {name}")
    choice = input(f"Enter choice [1-{len(companies)}] default 1: ").strip() or "1"
    try:
        idx = int(choice)
        company_key = companies[idx-1]
    except Exception:
        print("Invalid company choice. Exiting.")
        sys.exit(1)
    config = get_company_config(company_key)
    full_code = config.get("full_code")
    crawler_cls = CRAWLER_MAP.get(company_key)
    if not crawler_cls:
        print(f"No crawler for '{company_key}'. Exiting.")
        sys.exit(1)
    crawler = crawler_cls(full_code, config)
    # choose section(s)
    crawler.print_sections()
    report_input = input("Enter choice(s), separated by comma (default 1): ").strip() or "1"
    report_types = [r.strip() for r in report_input.split(',') if r.strip()]
    # input keywords interactively
    keywords = []
    idx = 1
    while True:
        kw = input(f'Please enter keyword {idx} (blank to finish): ').strip()
        if not kw:
            break
        keywords.append(kw)
        idx += 1
    if not keywords:
        print('No keywords provided. Exiting.')
        sys.exit(0)
    start_date = input('Enter earliest publish date (YYYY-MM-DD) or leave blank: ').strip() or None
    end_date = input('Enter latest publish date (YYYY-MM-DD) or leave blank: ').strip() or None
    # dispatch each selected section
    for rt in report_types:
        crawler.run_section(rt, keywords, BASE_DIR, start_date=start_date, end_date=end_date)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Interrupted by user. Exiting.")
        sys.exit(0)