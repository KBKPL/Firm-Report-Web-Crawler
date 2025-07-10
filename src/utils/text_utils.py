"""
Text utilities: splitting Chinese sentences, paragraph extraction, sanitization.
"""
import re


def find_paragraphs_with_keyword(text: str, keyword: str) -> list[str]:
    """Extract paragraphs containing keyword by splitting on blank lines."""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    blocks = [blk.strip() for blk in re.split(r'\n\s*\n+', text) if blk.strip()]
    keyword_lower = keyword.lower()
    return [blk for blk in blocks if keyword_lower in blk.lower()]

def sanitize_text(text: str) -> str:
    """Remove control characters except tab and newline."""
    return ''.join(ch for ch in text if ch in ('\t','\n') or ord(ch) >= 32)
