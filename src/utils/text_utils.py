"""
Text utilities: splitting Chinese sentences, paragraph extraction, sanitization.
"""
import re
from typing import List, Tuple


def find_paragraphs_with_keyword(text: str, keyword: str) -> list[str]:
    """Extract paragraphs containing keyword by splitting on blank lines."""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    blocks = [blk.strip() for blk in re.split(r'\n\s*\n+', text) if blk.strip()]
    keyword_lower = keyword.lower()
    return [blk for blk in blocks if keyword_lower in blk.lower()]


def sanitize_text(text: str) -> str:
    """Remove control characters except tab and newline."""
    return ''.join(ch for ch in text if ch in ('\t','\n') or ord(ch) >= 32)


def is_chinese_char(ch: str) -> bool:
    """Return True if a character is a Chinese character."""
    return '\u4e00' <= ch <= '\u9fff'


def generate_variants(keyword: str) -> List[str]:
    """Generate keyword variants with optional spaces between Chinese characters."""
    segments: List[Tuple[str, str]] = []
    i = 0
    while i < len(keyword):
        ch = keyword[i]
        if is_chinese_char(ch):
            start = i
            while i < len(keyword) and is_chinese_char(keyword[i]):
                i += 1
            run = keyword[start:i]
            spaced = ' '.join(run) if len(run) >= 2 else run
            segments.append((run, spaced))
        else:
            start = i
            while i < len(keyword) and not is_chinese_char(keyword[i]):
                i += 1
            run = keyword[start:i]
            segments.append((run, run))
    orig = ''.join(seg[0] for seg in segments)
    spaced_all = ''.join(seg[1] for seg in segments)
    variants = [orig]
    if spaced_all != orig:
        variants.append(spaced_all)
    return variants
