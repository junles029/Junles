from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

from .utils import ensure_dir, sanitize_filename, write_text



def render_markdown(
    title: str,
    source_url: str,
    metadata: Dict[str, object],
    summary: Dict[str, object],
    transcript_relpath: str,
    graph_mermaid_relpath: str,
    graph_json_relpath: str,
) -> str:
    tags = summary.get('tags', []) or []
    site = metadata.get('extractor_key') or metadata.get('extractor') or 'unknown'
    video_id = metadata.get('id') or ''
    uploader = metadata.get('uploader') or metadata.get('channel') or ''
    published = metadata.get('upload_date') or ''
    if published and len(str(published)) == 8:
        published = f'{str(published)[:4]}-{str(published)[4:6]}-{str(published)[6:8]}'

    lines: List[str] = []
    lines.extend([
        '---',
        f'title: "{title.replace("\"", "'")}"',
        f'source_url: "{source_url}"',
        f'site: "{site}"',
        f'video_id: "{video_id}"',
        f'uploader: "{str(uploader).replace("\"", "'")}"',
        f'published_at: "{published}"',
        f'created_at: "{datetime.now().isoformat(timespec="seconds")}"',
        'tags:',
    ])
    for tag in tags:
        lines.append(f'  - "{str(tag).replace("\"", "'")}"')
    lines.append('---')
    lines.append('')
    lines.append(f'# {title}')
    lines.append('')
    lines.append('## 概览')
    lines.append('')
    lines.append(str(summary.get('executive_summary', '')).strip() or '暂无概览')
    lines.append('')

    lines.append('## 关键要点')
    lines.append('')
    for item in summary.get('key_points', []):
        lines.append(f'- {item}')
    if not summary.get('key_points'):
        lines.append('- 暂无')
    lines.append('')

    lines.append('## 行动项')
    lines.append('')
    for item in summary.get('action_items', []):
        lines.append(f'- {item}')
    if not summary.get('action_items'):
        lines.append('- 暂无')
    lines.append('')

    lines.append('## 章节拆解')
    lines.append('')
    for chapter in summary.get('chapters', []):
        heading = chapter.get('heading', '未命名章节')
        desc = chapter.get('summary', '')
        lines.append(f'### {heading}')
        lines.append('')
        lines.append(desc)
        lines.append('')
    if not summary.get('chapters'):
        lines.append('暂无章节信息')
        lines.append('')

    lines.append('## 图谱文件')
    lines.append('')
    lines.append(f'- Mermaid: `{graph_mermaid_relpath}`')
    lines.append(f'- JSON: `{graph_json_relpath}`')
    lines.append('')

    lines.append('## 转写文件')
    lines.append('')
    lines.append(f'- `{transcript_relpath}`')
    lines.append('')

    return '\n'.join(lines)



def ingest_to_kb(
    kb_root: Path,
    slug: str,
    title: str,
    source_url: str,
    metadata: Dict[str, object],
    summary: Dict[str, object],
    work_files: Iterable[Path],
) -> Path:
    month_dir = datetime.now().strftime('%Y-%m')
    target_dir = ensure_dir(kb_root / 'videos' / month_dir / sanitize_filename(slug))

    copied_paths: List[Path] = []
    for path in work_files:
        if not path.exists():
            continue
        target_path = target_dir / path.name
        shutil.copy2(path, target_path)
        copied_paths.append(target_path)

    transcript_rel = 'transcript.txt'
    graph_mermaid_rel = 'knowledge_graph.mmd'
    graph_json_rel = 'knowledge_graph.json'

    note = render_markdown(
        title=title,
        source_url=source_url,
        metadata=metadata,
        summary=summary,
        transcript_relpath=transcript_rel,
        graph_mermaid_relpath=graph_mermaid_rel,
        graph_json_relpath=graph_json_rel,
    )
    note_path = target_dir / 'note.md'
    write_text(note_path, note)

    index_path = kb_root / 'index.jsonl'
    entry = {
        'title': title,
        'slug': slug,
        'source_url': source_url,
        'site': metadata.get('extractor_key') or metadata.get('extractor') or 'unknown',
        'video_id': metadata.get('id') or '',
        'tags': summary.get('tags', []),
        'path': str(note_path),
        'created_at': datetime.now().isoformat(timespec='seconds'),
    }
    with index_path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    return note_path
