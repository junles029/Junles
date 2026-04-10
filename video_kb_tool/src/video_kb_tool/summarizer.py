from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from typing import Dict, List, Optional

from .utils import chunk_text, split_sentences, unique_keep_order

try:
    import jieba
    import jieba.analyse
except Exception:  # pragma: no cover
    jieba = None


STOPWORDS = {
    '的', '了', '和', '是', '在', '就', '都', '而', '及', '与', '着', '或', '一个', '我们', '你', '我',
    '也', '要', '会', '把', '并', '并且', '如果', '这个', '那个', '然后', '因为', '所以', '就是', '进行',
    'to', 'of', 'the', 'and', 'is', 'in', 'on', 'for', 'with', 'that', 'this', 'it', 'as', 'be', 'are',
}



def _contains_chinese(text: str) -> bool:
    return bool(re.search(r'[\u4e00-\u9fff]', text))



def _tokenize(text: str) -> List[str]:
    if jieba and _contains_chinese(text):
        tokens = [w.strip() for w in jieba.cut(text) if w.strip()]
    else:
        tokens = re.findall(r'[A-Za-z]{3,}|\d+|[\u4e00-\u9fff]{2,}', text)
    return [t.lower() for t in tokens if t.lower() not in STOPWORDS and len(t.strip()) >= 2]



def _extract_keywords(text: str, top_k: int = 8) -> List[str]:
    if jieba and _contains_chinese(text):
        try:
            return unique_keep_order(jieba.analyse.extract_tags(text, topK=top_k))
        except Exception:
            pass
    counts = Counter(_tokenize(text))
    return [token for token, _ in counts.most_common(top_k)]



def _extractive_summary(text: str, max_points: int = 6) -> Dict[str, object]:
    sentences = split_sentences(text)
    if not sentences:
        return {
            'executive_summary': '',
            'key_points': [],
            'action_items': [],
            'tags': [],
            'chapters': [],
        }

    token_freq = Counter(_tokenize(text))
    scores = []
    for idx, sentence in enumerate(sentences):
        tokens = _tokenize(sentence)
        if not tokens:
            continue
        score = sum(token_freq[t] for t in tokens) / math.sqrt(len(tokens))
        scores.append((idx, score, sentence))

    top = sorted(scores, key=lambda x: x[1], reverse=True)[: max(max_points + 3, 6)]
    ordered = sorted(top, key=lambda x: x[0])
    best_sentences = [s for _, _, s in ordered]

    executive = ' '.join(best_sentences[:3]).strip()
    key_points = best_sentences[:max_points]

    action_pattern = re.compile(r'(建议|应该|需要|下一步|行动|优化|注意|务必|可以|TODO|todo)')
    action_items = [s for s in sentences if action_pattern.search(s)][:5]
    if not action_items:
        action_items = key_points[:2]

    chunks = chunk_text(text, max_chars=max(3000, len(text) // 3 or 3000))[:4]
    chapters = []
    for idx, chunk in enumerate(chunks, start=1):
        c_sentences = split_sentences(chunk)[:3]
        chapters.append({
            'heading': f'片段 {idx}',
            'summary': ' '.join(c_sentences),
        })

    return {
        'executive_summary': executive,
        'key_points': unique_keep_order(key_points)[:max_points],
        'action_items': unique_keep_order(action_items)[:5],
        'tags': _extract_keywords(text, top_k=8),
        'chapters': chapters,
    }



def _openai_summary(text: str, title: str, model: str) -> Dict[str, object]:
    try:
        from openai import OpenAI
    except Exception as exc:  # pragma: no cover
        raise RuntimeError('未安装 openai SDK。请执行: pip install openai') from exc

    if not os.getenv('OPENAI_API_KEY'):
        raise RuntimeError('未检测到 OPENAI_API_KEY，无法使用 OpenAI 总结器。')

    client = OpenAI()
    prompt = {
        'title': title,
        'transcript': text[:120000],
        'task': (
            '请基于转写内容输出 JSON，字段必须包含: '
            'executive_summary(string), key_points(array of string, 4-8条), '
            'action_items(array of string, 0-5条), tags(array of string, 3-8条), '
            'chapters(array of object, 每项含 heading 和 summary)。'
            '输出中文，避免空话。'
        ),
    }

    resp = client.chat.completions.create(
        model=model,
        response_format={'type': 'json_object'},
        messages=[
            {
                'role': 'system',
                'content': '你是擅长知识整理的视频内容分析助手，只输出合法 JSON。',
            },
            {
                'role': 'user',
                'content': json.dumps(prompt, ensure_ascii=False),
            },
        ],
        temperature=0.2,
    )
    content = resp.choices[0].message.content or '{}'
    data = json.loads(content)
    return {
        'executive_summary': data.get('executive_summary', ''),
        'key_points': unique_keep_order(data.get('key_points', []))[:8],
        'action_items': unique_keep_order(data.get('action_items', []))[:5],
        'tags': unique_keep_order(data.get('tags', []))[:8],
        'chapters': data.get('chapters', [])[:8],
    }



def summarize_text(
    text: str,
    title: str,
    provider: str = 'extractive',
    openai_model: str = 'gpt-4.1-mini',
) -> Dict[str, object]:
    if provider == 'openai':
        try:
            return _openai_summary(text=text, title=title, model=openai_model)
        except Exception:
            return _extractive_summary(text)
    return _extractive_summary(text)
