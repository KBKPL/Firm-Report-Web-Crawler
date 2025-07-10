"""
Main module for PDF keyword search and exporting matching paragraphs to a docx file.
"""

import logging
import sys
import os
from pathlib import Path
from crawler import crawl_broker_reports
from crawler import crawl_company_announcements, crawl_quarterly_performance

# Project root one level above src
BASE_DIR = Path(__file__).parent.parent

def main():
    # choose section(s)
    print("Select report section(s), separated by comma:")
    print("1. 季度业绩 (quarterly performance)")
    print("2. 公司公告 (company announcements)")
    print("3. 券商报告 (broker reports)")
    report_input = input("Enter choice(s) (e.g. 1,2 or 1, 2) default 1 (季度业绩): ").strip() or "1"
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
        if rt == '1':  # quarterly performance
            output_dir = str(BASE_DIR / 'quarterly performance')
            try:
                generated = crawl_quarterly_performance(code, keywords, output_dir=output_dir, start_date=start_date, end_date=end_date)
                if generated:
                    print("Generated quarterly performance docs:")
                    for kw, path in generated.items():
                        print(f"  {kw}: {path}")
                else:
                    print("No quarterly performance docs generated.")
            except Exception as e:
                print(f"Error during quarterly performance crawl: {e}")
        elif rt == '2':  # company announcements
            output_dir = str(BASE_DIR / 'company announcements')
            try:
                generated = crawl_company_announcements(code, keywords, output_dir=output_dir, start_date=start_date, end_date=end_date)
                if generated:
                    print("Generated company announcements docs:")
                    for kw, path in generated.items():
                        print(f"  {kw}: {path}")
                else:
                    print("No company announcements docs generated.")
            except Exception as e:
                print(f"Error during company announcements crawl: {e}")
        elif rt == '3':  # broker reports
            output_dir = str(BASE_DIR / 'broker reports')
            try:
                generated = crawl_broker_reports(code, keywords, output_dir=output_dir, start_date=start_date, end_date=end_date)
                if generated:
                    print("Generated broker reports docs:")
                    for kw, path in generated.items():
                        print(f"  {kw}: {path}")
                else:
                    print("No broker reports docs generated.")
            except Exception as e:
                print(f"Error during broker reports crawl: {e}")
        else:
            print(f"Unknown section '{rt}', skipping.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Interrupted by user. Exiting.")
        sys.exit(0)