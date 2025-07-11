#!/usr/bin/env python3
"""
test.py: Download the first company announcement PDF for Ganfeng Lithium.
Requires: requests, beautifulsoup4, pdftext
Usage: python test.py
"""
import requests
from bs4 import BeautifulSoup
import os
import subprocess
import tempfile
from docx import Document
from src.utils.text_utils import sanitize_text, find_paragraphs_with_keyword
from src.utils.docx_utils import add_keyword_paragraphs

BASE_URL = 'https://www.ganfenglithium.com'
LISTING_PATH = '/index.php/Home/Index/ir4/p/1.html'
LISTING_URL = BASE_URL + LISTING_PATH

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
}

def download_first_report(output_dir='downloads'):
    os.makedirs(output_dir, exist_ok=True)
    # fetch listing page with browser-like headers
    resp = requests.get(LISTING_URL, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    # find the first announcement item
    items = soup.find_all('div', class_='irggfl')
    if not items:
        print('No announcement items found.')
        return
    item = items[0]
    font_link = item.find('a', class_='irfont')
    if not font_link or not font_link.get('href'):
        print('Announcement link not found.')
        return
    title = font_link.get_text(strip=True)
    href = font_link['href']
    detail_url = href if href.startswith('http') else BASE_URL + href
    print(f'Found announcement: {title}\nDetail page: {detail_url}')

    # fetch detail page
    resp2 = requests.get(detail_url, headers=HEADERS)
    resp2.raise_for_status()
    soup2 = BeautifulSoup(resp2.text, 'html.parser')

    # find PDF download link
    a_pdf = soup2.find('a', href=lambda href: href and href.lower().endswith('.pdf'))
    if not a_pdf:
        print('PDF download link not found.')
        return
    pdf_url = a_pdf['href']
    if pdf_url.startswith('/'):
        pdf_url = BASE_URL + pdf_url
    print(f'Downloading PDF: {pdf_url}')

    # download PDF
    pdf_resp = requests.get(pdf_url, headers=HEADERS)
    pdf_resp.raise_for_status()
    filename = os.path.join(output_dir, os.path.basename(pdf_url))
    with open(filename, 'wb') as f:
        f.write(pdf_resp.content)
    print(f'Saved PDF to {filename}')
    return
    # extract text via pdftext
    tmp_txt = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    tmp_txt.close()
    keyword = '江西'
    try:
        subprocess.run(["pdftext", filename, "--out_path", tmp_txt.name], check=True)
        with open(tmp_txt.name, "r", encoding="utf-8") as f_txt:
            text = f_txt.read()
    except Exception as e:
        print("pdftext failed:", e)
        return
    finally:
        os.remove(tmp_txt.name)
    # sanitize and split into paragraphs
    text = sanitize_text(text)
    paras = find_paragraphs_with_keyword(text, keyword)
    # filter paragraphs containing Chinese characters or fullwidth punctuation (， or 。)
    paras = [p for p in paras if any('\u4e00' <= ch <= '\u9fff' for ch in p) or '，' in p or '。' in p]
    if not paras:
        print('No matching paragraphs with Traditional Chinese.')
        return
    # build and save DOCX with highlights and hyperlink
    doc = Document()
    add_keyword_paragraphs(doc, paras, keyword, pdf_url)
    docx_path = os.path.join(output_dir, f'{keyword}.docx')
    doc.save(docx_path)
    print(f'Saved filtered docx to {docx_path}')


if __name__ == '__main__':
    download_first_report()
