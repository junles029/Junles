from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict

from .runtime import resolve_paths
from .utils import ensure_dir

SETTINGS_FILE = 'desktop_settings.json'


@dataclass
class DesktopSettings:
    workdir: str = ''
    kb_root: str = ''
    summary_provider: str = 'extractive'
    openai_model: str = 'gpt-4.1-mini'
    whisper_model: str = 'small'
    language: str = 'zh'
    device: str = 'cpu'
    compute_type: str = 'int8'
    prefer_subs: bool = True
    keep_video: bool = True



def settings_path() -> Path:
    paths = resolve_paths()
    ensure_dir(paths.config_dir)
    return paths.config_dir / SETTINGS_FILE



def load_settings() -> DesktopSettings:
    path = settings_path()
    if not path.exists():
        return DesktopSettings()
    try:
        payload: Dict[str, Any] = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return DesktopSettings()
    data = asdict(DesktopSettings())
    data.update({k: v for k, v in payload.items() if k in data})
    return DesktopSettings(**data)



def save_settings(settings: DesktopSettings) -> Path:
    path = settings_path()
    path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding='utf-8')
    return path
