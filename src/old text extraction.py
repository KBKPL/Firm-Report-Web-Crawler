from pdf2docx import Converter

# pdf_file = '/path/to/sample.pdf'
# docx_file = 'path/to/sample.docx'
pdf_file = 'D:/Firm Info/sample.pdf'
# docx_file = 'D:/Firm Info/sample.docx'

from docling.document_converter import DocumentConverter

source = pdf_file  # PDF path or URL
converter = DocumentConverter()
result = converter.convert(source)

# text = result.document.export_to_text()
result = result.document.export_to_text()
for p in result.paragraphs:
    print(p.text.strip())
    print(p.text.strip().encode('utf-8').decode('utf-8-sig'))

# print(result.document.export_to_text())

# print(result.document.export_to_markdown())
