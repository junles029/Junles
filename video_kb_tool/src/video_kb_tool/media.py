from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .runtime import extend_process_path, resolve_ffmpeg_executable
from .utils import ensure_dir


class FFmpegNotFoundError(EnvironmentError):
    pass



def ffmpeg_command() -> str:
    extend_process_path()
    bundled = resolve_ffmpeg_executable()
    if bundled and bundled.exists():
        return str(bundled)
    system_path = shutil.which('ffmpeg')
    if system_path:
        return system_path
    raise FFmpegNotFoundError('未检测到 ffmpeg。请安装系统 ffmpeg，或将 ffmpeg 放到 tools/ffmpeg/bin/ 目录下。')



def ensure_ffmpeg() -> None:
    ffmpeg_command()



def extract_audio(video_path: Path, output_dir: Path) -> Path:
    cmd_ffmpeg = ffmpeg_command()
    ensure_dir(output_dir)
    audio_path = output_dir / f'{video_path.stem}.mp3'
    cmd = [
        cmd_ffmpeg, '-y', '-i', str(video_path),
        '-vn', '-ac', '1', '-ar', '16000', '-b:a', '128k',
        str(audio_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    return audio_path
