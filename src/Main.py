"""
Main module for PDF keyword search and exporting matching paragraphs to a docx file.
"""

import logging
import sys
from crawler import crawl_company

def main():
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
    crawl_company(code, keywords, start_date=start_date, end_date=end_date)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Interrupted by user. Exiting.")
        sys.exit(0)