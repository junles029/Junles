from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC = ROOT / 'video_kb_tool.spec'
DIST = ROOT / 'dist'
BUILD = ROOT / 'build'


def main() -> int:
    if not SPEC.exists():
        print(f'未找到 spec 文件: {SPEC}')
        return 1
    for path in (DIST, BUILD):
        if path.exists():
            shutil.rmtree(path)
    cmd = [sys.executable, '-m', 'PyInstaller', '--noconfirm', str(SPEC)]
    print('执行:', ' '.join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)
    print(f'打包完成，输出目录: {DIST}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
