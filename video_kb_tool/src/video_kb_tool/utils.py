from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Iterable, List

try:
    from slugify import slugify as _slugify
except Exception:  # pragma: no cover
    _slugify = None


CHINESE_SENTENCE_SEP = re.compile(r'(?<=[。！？!?；;])\s*')
EN_SENTENCE_SEP = re.compile(r'(?<=[.!?])\s+')
TAG_RE = re.compile(r'<[^>]+>')
SPACE_RE = re.compile(r'\s+')


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode('utf-8')).hexdigest()



def safe_slug(text: str, fallback: str = 'video') -> str:
    text = (text or '').strip()
    if _slugify:
        candidate = _slugify(text, lowercase=True, separator='-')
        if candidate:
            return candidate[:80]
    candidate = re.sub(r'[^\w\u4e00-\u9fff-]+', '-', text, flags=re.UNICODE)
    candidate = re.sub(r'-{2,}', '-', candidate).strip('-_')
    return (candidate[:80] or fallback)



def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]+', '_', name).strip()[:180]



def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')



def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding='utf-8')



def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')



def split_sentences(text: str) -> List[str]:
    text = SPACE_RE.sub(' ', text).strip()
    if not text:
        return []
    chunks = []
    for part in CHINESE_SENTENCE_SEP.split(text):
        if not part:
            continue
        subparts = EN_SENTENCE_SEP.split(part)
        chunks.extend([p.strip() for p in subparts if p.strip()])
    return chunks



def chunk_text(text: str, max_chars: int = 6000) -> List[str]:
    sentences = split_sentences(text)
    chunks: List[str] = []
    current: List[str] = []
    size = 0
    for sentence in sentences:
        if size + len(sentence) > max_chars and current:
            chunks.append(' '.join(current))
            current = [sentence]
            size = len(sentence)
        else:
            current.append(sentence)
            size += len(sentence)
    if current:
        chunks.append(' '.join(current))
    return chunks



def strip_subtitle_markup(text: str) -> str:
    text = TAG_RE.sub('', text)
    text = re.sub(r'\{[^}]*\}', '', text)
    text = text.replace('&nbsp;', ' ')
    return SPACE_RE.sub(' ', text).strip()



def unique_keep_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        item = item.strip()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out
