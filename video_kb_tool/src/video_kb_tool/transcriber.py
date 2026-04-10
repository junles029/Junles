from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .utils import read_text, split_sentences, strip_subtitle_markup, unique_keep_order, write_json, write_text


TIME_RE = re.compile(r'^\s*\d{2}:\d{2}:\d{2}[,.]\d{1,3}\s+-->\s+\d{2}:\d{2}:\d{2}[,.]\d{1,3}')
VTT_TIME_RE = re.compile(r'^\s*\d{2}:\d{2}[.:]\d{2}[.]\d{1,3}\s+-->\s+\d{2}:\d{2}[.:]\d{2}[.]\d{1,3}')
NUM_RE = re.compile(r'^\d+$')



def _subtitle_to_transcript(text: str) -> str:
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith('WEBVTT'):
            continue
        if TIME_RE.match(line) or VTT_TIME_RE.match(line):
            continue
        if NUM_RE.match(line):
            continue
        lines.append(strip_subtitle_markup(line))
    return '\n'.join(unique_keep_order(lines))



def load_transcript_from_subtitle(path: Path) -> str:
    return _subtitle_to_transcript(read_text(path))



def pick_best_subtitle(subtitle_paths: List[Path]) -> Optional[Path]:
    if not subtitle_paths:
        return None
    preferences = ['zh-hans', 'zh-cn', 'zh', 'en']
    lowered = {p: p.name.lower() for p in subtitle_paths}
    for pref in preferences:
        for path, name in lowered.items():
            if pref in name:
                return path
    return subtitle_paths[0]



def transcribe_audio(
    audio_path: Path,
    output_dir: Path,
    model_size: str = 'small',
    language: Optional[str] = None,
    device: str = 'cpu',
    compute_type: str = 'int8',
) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:  # pragma: no cover
        raise RuntimeError('未安装 faster-whisper。请执行: pip install faster-whisper') from exc

    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments_iter, info = model.transcribe(
        str(audio_path),
        beam_size=5,
        language=language,
        vad_filter=True,
    )

    segments: List[Dict[str, Any]] = []
    transcript_lines: List[str] = []
    for seg in segments_iter:
        item = {
            'start': round(seg.start, 3),
            'end': round(seg.end, 3),
            'text': seg.text.strip(),
        }
        segments.append(item)
        transcript_lines.append(item['text'])

    transcript = '\n'.join(transcript_lines).strip()
    write_json(output_dir / 'segments.json', segments)
    info_payload = {
        'language': getattr(info, 'language', None),
        'language_probability': getattr(info, 'language_probability', None),
        'duration': getattr(info, 'duration', None),
        'duration_after_vad': getattr(info, 'duration_after_vad', None),
    }
    write_json(output_dir / 'transcription_info.json', info_payload)
    write_text(output_dir / 'transcript.txt', transcript)
    return transcript, segments, info_payload



def save_subtitle_transcript(subtitle_path: Path, output_dir: Path) -> str:
    transcript = load_transcript_from_subtitle(subtitle_path)
    write_text(output_dir / 'transcript.txt', transcript)
    pseudo_segments = [
        {'start': None, 'end': None, 'text': sentence}
        for sentence in split_sentences(transcript)
    ]
    write_json(output_dir / 'segments.json', pseudo_segments)
    write_json(output_dir / 'transcription_info.json', {'source': 'subtitle', 'subtitle_file': str(subtitle_path)})
    return transcript
