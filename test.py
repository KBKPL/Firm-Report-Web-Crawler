#!/usr/bin/env python3
"""
test.py: Download the first quarterly performance PDF for 盛新锂能 (Shengxin Lithium).
Requires: requests, beautifulsoup4
Usage: python test.py
"""
import requests
from bs4 import BeautifulSoup
import os
import json
import html
import subprocess
import tempfile
from docx import Document
from src.utils.text_utils import sanitize_text, find_paragraphs_with_keyword
from src.utils.docx_utils import add_keyword_paragraphs

BASE_URL = 'https://www.cxlithium.com'
LISTING_URL = BASE_URL + '/download/1712104669691871232-0-10.html'

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Referer": LISTING_URL
}

def download_first_quarterly(output_dir='downloads'):
    os.makedirs(output_dir, exist_ok=True)
    # fetch listing page with browser-like headers
    resp = requests.get(LISTING_URL, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    # find the first item
    items = soup.find_all('div', class_='cbox-2 p_loopitem')
    if not items:
        print('No quarterly items found.')
        return
    first = items[0]
    title = first.find('h1', class_='e_h1-4 s_subtitle').get_text(strip=True)
    date = first.find('p', class_='e_timeFormat-18 s_title').get_text(strip=True)

    # parse embedded JSON for PDF URL
    input_tag = first.find('input', attrs={'name': 'fileList'})
    if not input_tag or not input_tag.get('value'):
        print('fileList input not found.')
        return
    raw = input_tag['value']
    unesc = html.unescape(raw)
    try:
        files = json.loads(unesc)
        file_info = files[0]
    except Exception as e:
        print('Failed to parse fileList JSON:', e)
        return
    if not files:
        print('No files in fileList.')
        return
    pdf_url = file_info.get('fileUrl')
    print(f'Downloading first report: "{title}" ({date})')
    r2 = requests.get(pdf_url, headers=HEADERS)
    r2.raise_for_status()
    filename = os.path.join(output_dir, file_info.get('title') or os.path.basename(pdf_url))
    with open(filename, 'wb') as f:
        f.write(r2.content)
    print(f'Saved PDF to {filename}')
    # extract text via pdftext
    tmp_txt = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    tmp_txt.close()
    try:
        subprocess.run(["pdftext", filename, "--out_path", tmp_txt.name], check=True)
        text = open(tmp_txt.name, "r", encoding="utf-8").read()
    except Exception as e:
        print("pdftext extraction failed:", e)
        return
    finally:
        os.remove(tmp_txt.name)
    # filter paragraphs for '成都'
    text = sanitize_text(text)
    paras = find_paragraphs_with_keyword(text, "公司")
    paras = [p for p in paras if any('\u4e00' <= ch <= '\u9fff' or ch in '，。' for ch in p)]
    if not paras:
        print('No matching paragraphs for 成都.')
        return
    doc = Document()
    add_keyword_paragraphs(doc, paras, "成都", pdf_url)
    docx_path = os.path.join(output_dir, "成都.docx")
    doc.save(docx_path)
    print(f'Saved filtered docx to {docx_path}')

if __name__ == '__main__':
    download_first_quarterly()
