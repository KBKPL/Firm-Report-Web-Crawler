# Future Maintenance Guide

This document outlines steps for ongoing maintenance of the crawler project.

## 1. Adding a New Company Crawler

1. **Update Configuration**  
   - Open `config.json` and add a new key for the company (matching its lowercase code).  
   - Define `full_code`, `page_size`, and URL templates (e.g., `quarterly_url`, `company_announcement_url`, `dynamic_url`) with `{page}` or `{offset}` placeholders.

2. **Create Crawler Class**  
   - Under `src/crawlers/`, create `<company>_crawler.py`.  
   - Define class `XxxCrawler(CompanyCrawler)`.  
   - Add entry in `SECTIONS` mapping:
     - **Domestic**: `(Chinese name, English label, method_name)`
     - **Foreign**: `(English label, method_name)`
   - Reuse generic utilities in `src/utils` (http_utils, pdf_utils, text_utils, docx_utils) for common tasks; only implement new helpers in the crawler when necessary.

3. **Implement Page Fetch Helpers**  
   - For each section (e.g., quarterly, announcements, dynamic), add `fetch_<section>_page(page_index: int) -> List[Dict]`.  
   - Use BeautifulSoup to parse the list page, extract `title`, `publishDate`, and `pdf_url` or `url`.  
   - Ensure to leverage existing utilities (`session`, parsing, JSON handling) from `src/utils` where applicable.

4. **Implement Crawl Methods**  
   - Leverage generic utilities in `src/utils` (`session`, `pdf_utils`, `text_utils`, `docx_utils`) for HTTP requests, PDF download, text extraction, sanitization, and DOCX generation. Only implement site-specific crawl logic in the crawler class when necessary.
   - For each section, define `crawl_<section>(keywords, output_dir, start_date, end_date) -> Dict[str, str]`.
   - Loop pages: call fetch helper, stop on empty or date bounds, obtain content, sanitize, extract paragraphs with keywords, and write to DOCX via `add_keyword_paragraphs` + `save_crawler_docx`.

5. **Site-Specific Helpers**  
   - First try generic download and extraction in `src/utils/http_utils` and `src/utils/pdf_utils`.  
   - If the site needs custom headers (e.g., Referer), URL encoding, or cookies, then add `_download_<company>_pdf` and `_extract_text_from_<company>_pdf` inside the company crawler class.

6. **Testing**  
   - Add a simple test script under `src/test_<company>.py` using `session` to fetch one page and verify selectors.  
   - Run end-to-end crawl locally (e.g., `crawler.run_section("1", [...])`) and inspect generated DOCX.

## 2. Updating an Existing Crawler After Site Changes

1. **Detect Breakage**  
   - Monitor logs for parsing errors, HTTP errors (403/404), or empty result sets.

2. **Review HTML Changes**  
   - Load the site in browser, inspect new page structure, note changed class names or element hierarchy.

3. **Update Selectors & Parsing**  
   - In `fetch_<section>_page`, adjust `soup.find_all(...)` and tag lookups to match updated classes or tags.  
   - If JSON payload has new fields, update `_parse_file_list_item` or equivalent.

4. **Update URL Templates**  
   - If patterns changed (e.g., new query parameters, path segments), modify relevant `*_url` in `config.json`.

5. **Adjust Page Size or Pagination**  
   - If page size or offset logic changed, update `page_size` or `dynamic_page_size` in config and code.

6. **Update Site-Specific Download Logic**  
   - If server now requires new headers (e.g., `Referer`, auth tokens), update `_download_<company>_pdf` or session defaults in `src/utils/http_utils.py`.

7. **Re-run Tests & Crawl**  
   - Update or add tests under `src/`.  
   - Execute `crawler.run_section` for each section to verify output.  
   - Inspect generated DOCX and logs.

8. **Document Changes**  
   - Note the maintenance steps in this guide and commit changes with clear commit messages.
