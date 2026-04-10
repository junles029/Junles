from __future__ import annotations

import platform
import shutil
import sys
from pathlib import Path
from typing import Dict, List

from .runtime import resolve_ffmpeg_executable, resolve_paths

REQUIRED_MODULES = [
    ('yt_dlp', '视频下载'),
    ('faster_whisper', '音频转写'),
    ('rich', 'CLI 展示'),
    ('jieba', '中文关键词抽取'),
]
OPTIONAL_MODULES = [
    ('openai', 'OpenAI 总结'),
    ('torch', 'GPU/加速能力'),
]



def _module_status(module_name: str, purpose: str, required: bool) -> Dict[str, str]:
    try:
        __import__(module_name)
        status = 'ok'
        detail = '已安装'
    except Exception as exc:
        status = 'missing' if required else 'optional-missing'
        detail = f"{'缺失' if required else '未安装'}: {exc.__class__.__name__}"
    return {
        'name': module_name,
        'purpose': purpose,
        'status': status,
        'detail': detail,
        'required': 'yes' if required else 'no',
    }



def collect_env_status() -> Dict[str, object]:
    paths = resolve_paths()
    modules: List[Dict[str, str]] = []
    for module_name, purpose in REQUIRED_MODULES:
        modules.append(_module_status(module_name, purpose, required=True))
    for module_name, purpose in OPTIONAL_MODULES:
        modules.append(_module_status(module_name, purpose, required=False))

    bundled_ffmpeg = resolve_ffmpeg_executable(paths)
    ffmpeg_path = str(bundled_ffmpeg) if bundled_ffmpeg else shutil.which('ffmpeg')
    ffmpeg_source = 'bundled' if bundled_ffmpeg else ('system-path' if ffmpeg_path else 'missing')

    return {
        'python_version': sys.version.split()[0],
        'platform': platform.platform(),
        'executable': sys.executable,
        'app_root': str(paths.root_dir),
        'user_data_dir': str(paths.user_data_dir),
        'runs_dir': str(paths.runs_dir),
        'knowledge_base_dir': str(paths.knowledge_base_dir),
        'logs_dir': str(paths.logs_dir),
        'config_dir': str(paths.config_dir),
        'tools_dir': str(paths.tools_dir),
        'frozen': 'yes' if getattr(sys, 'frozen', False) else 'no',
        'ffmpeg': {
            'status': 'ok' if ffmpeg_path else 'missing',
            'path': ffmpeg_path or '',
            'source': ffmpeg_source,
        },
        'modules': modules,
    }



def format_env_status(status: Dict[str, object]) -> str:
    lines = []
    lines.append(f"Python: {status['python_version']}")
    lines.append(f"Platform: {status['platform']}")
    lines.append(f"Executable: {status['executable']}")
    lines.append(f"Frozen: {status['frozen']}")
    lines.append(f"App root: {status['app_root']}")
    lines.append(f"User data: {status['user_data_dir']}")
    ffmpeg = status['ffmpeg']
    lines.append(f"ffmpeg: {ffmpeg['status']} ({ffmpeg['source']}) {ffmpeg['path']}")
    lines.append('')
    lines.append('Modules:')
    for module in status['modules']:
        prefix = '[必需]' if module['required'] == 'yes' else '[可选]'
        lines.append(f"- {prefix} {module['name']} ({module['purpose']}): {module['status']} - {module['detail']}")
    return '\n'.join(lines)
