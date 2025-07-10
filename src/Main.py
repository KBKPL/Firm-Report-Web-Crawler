"""
Main module for PDF keyword search and exporting matching paragraphs to a docx file.
"""

import logging
import sys
import os
from pathlib import Path
from crawler import crawl_company
from crawler import crawl_company_reports

# Project root one level above src
BASE_DIR = Path(__file__).parent.parent

def main():
    # choose section(s)
    print("Select report section(s), separated by comma:")
    print("1. 券商报告 (broker reports)")
    print("2. 公司公告 (company announcements)")
    report_input = input("Enter choice(s) (e.g. 1,2 or 1, 2) default 1: ").strip() or "1"
    report_types = [r.strip() for r in report_input.split(',') if r.strip()]
    code = input('Enter company code (e.g. sz002738): ').strip() or 'sz002738'
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
        if rt == '1':
            # broker reports
            output_dir = str(BASE_DIR / 'broker reports')
            crawl_company(code, keywords, output_dir=output_dir, start_date=start_date, end_date=end_date)
        elif rt == '2':
            # company announcements
            output_dir = str(BASE_DIR / 'company announcements')
            crawl_company_reports(code, keywords, output_dir=output_dir, start_date=start_date, end_date=end_date)
        else:
            print(f"Unknown section '{rt}', skipping.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Interrupted by user. Exiting.")
        sys.exit(0)