# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH)
block_cipher = None

hiddenimports = []
for pkg in ['yt_dlp', 'faster_whisper', 'jieba', 'rich']:
    hiddenimports += collect_submodules(pkg)

datas = []
for pkg in ['yt_dlp', 'faster_whisper', 'jieba']:
    datas += collect_data_files(pkg)

extra_datas = [
    ('src', 'src'),
    ('README.md', '.'),
    ('packaging/windows/README-WINDOWS.md', 'packaging/windows'),
    ('packaging/windows/installer.iss', 'packaging/windows'),
    ('tools', 'tools'),
]

for src, dest in extra_datas:
    src_path = ROOT / src
    if src_path.exists():
        datas.append((str(src_path), dest))

a = Analysis(
    ['run_desktop.py'],
    pathex=[str(ROOT), str(ROOT / 'src')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VideoKBDesktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VideoKBDesktop',
)
