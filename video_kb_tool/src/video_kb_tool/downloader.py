from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from yt_dlp import YoutubeDL

from .utils import ensure_dir, write_json


@dataclass
class DownloadResult:
    video_path: Path
    metadata_path: Path
    metadata: Dict[str, Any]
    subtitle_paths: List[Path]


class RightsConfirmationError(PermissionError):
    pass



def _discover_subtitles(work_dir: Path) -> List[Path]:
    exts = {'.vtt', '.srt', '.ass'}
    return sorted([p for p in work_dir.iterdir() if p.is_file() and p.suffix.lower() in exts])



def _guess_video_path(work_dir: Path, info: Dict[str, Any]) -> Path:
    candidates = [
        p for p in work_dir.iterdir()
        if p.is_file() and p.suffix.lower() in {'.mp4', '.mkv', '.webm', '.mov', '.m4v'}
    ]
    if not candidates:
        raise FileNotFoundError('下载完成后未发现视频文件，请确认 ffmpeg 已安装且目标站点受支持。')

    video_id = str(info.get('id', ''))
    if video_id:
        for path in candidates:
            if video_id in path.name:
                return path
    return max(candidates, key=lambda p: p.stat().st_mtime)



def download_video(url: str, work_dir: Path, confirm_rights: bool) -> DownloadResult:
    if not confirm_rights:
        raise RightsConfirmationError(
            '出于合规考虑，需要显式确认你有权下载该视频，或平台条款允许下载/归档。请加入 --confirm-rights。'
        )

    ensure_dir(work_dir)
    ydl_opts = {
        'outtmpl': str(work_dir / '%(title).180B [%(id)s].%(ext)s'),
        'format': 'bv*+ba/b',
        'format_sort': ['res:desc', 'fps:desc', 'hdr:12', 'vcodec:av1', 'vcodec:vp9.2', 'vcodec:hevc'],
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['zh-Hans', 'zh-CN', 'zh', 'en'],
        'quiet': False,
        'no_warnings': False,
        'ignoreerrors': False,
        'restrictfilenames': False,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_path = _guess_video_path(work_dir, info)
        metadata_path = work_dir / 'video_metadata.json'
        write_json(metadata_path, info)

    subtitle_paths = _discover_subtitles(work_dir)
    return DownloadResult(
        video_path=video_path,
        metadata_path=metadata_path,
        metadata=info,
        subtitle_paths=subtitle_paths,
    )
