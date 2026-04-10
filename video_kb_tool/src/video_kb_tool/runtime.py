from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from .utils import ensure_dir

APP_NAME = 'VideoKBDesktop'


@dataclass(frozen=True)
class AppPaths:
    root_dir: Path
    resource_dir: Path
    user_data_dir: Path
    runs_dir: Path
    knowledge_base_dir: Path
    logs_dir: Path
    config_dir: Path
    tools_dir: Path



def is_frozen() -> bool:
    return bool(getattr(sys, 'frozen', False))



def resource_base() -> Path:
    if is_frozen() and hasattr(sys, '_MEIPASS'):
        return Path(getattr(sys, '_MEIPASS'))
    return Path(__file__).resolve().parents[2]



def app_root() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]



def default_user_data_dir() -> Path:
    if os.name == 'nt':
        base = Path(os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or app_root())
        return base / APP_NAME
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / APP_NAME
    return Path.home() / '.local' / 'share' / APP_NAME



def resolve_paths() -> AppPaths:
    root = app_root()
    resource_dir = resource_base()
    user_data = ensure_dir(default_user_data_dir()) if is_frozen() else root
    config_dir = ensure_dir(user_data / 'config')
    runs_dir = ensure_dir(user_data / 'runs')
    kb_dir = ensure_dir(user_data / 'knowledge_base')
    logs_dir = ensure_dir(user_data / 'logs')
    tools_dir = root / 'tools'
    ensure_dir(tools_dir)
    return AppPaths(
        root_dir=root,
        resource_dir=resource_dir,
        user_data_dir=user_data,
        runs_dir=runs_dir,
        knowledge_base_dir=kb_dir,
        logs_dir=logs_dir,
        config_dir=config_dir,
        tools_dir=tools_dir,
    )



def candidate_ffmpeg_paths(paths: Optional[AppPaths] = None) -> Iterable[Path]:
    paths = paths or resolve_paths()
    names = ['ffmpeg.exe', 'ffmpeg'] if os.name == 'nt' else ['ffmpeg']
    candidates = [
        paths.tools_dir / 'ffmpeg' / 'bin',
        paths.root_dir / 'ffmpeg' / 'bin',
        paths.resource_dir / 'tools' / 'ffmpeg' / 'bin',
    ]
    for folder in candidates:
        for name in names:
            yield folder / name



def resolve_ffmpeg_executable(paths: Optional[AppPaths] = None) -> Optional[Path]:
    for candidate in candidate_ffmpeg_paths(paths):
        if candidate.exists():
            return candidate
    return None



def extend_process_path(paths: Optional[AppPaths] = None) -> None:
    paths = paths or resolve_paths()
    additions = []
    ffmpeg = resolve_ffmpeg_executable(paths)
    if ffmpeg:
        additions.append(str(ffmpeg.parent))
    current = os.environ.get('PATH', '')
    extras = [p for p in additions if p and p not in current]
    if extras:
        os.environ['PATH'] = os.pathsep.join(extras + [current]) if current else os.pathsep.join(extras)
