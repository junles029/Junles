$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..

if (-not (Test-Path .venv)) {
    py -3 -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements-packaging.txt
python build_desktop.py
Write-Host "Build complete. See dist\VideoKBDesktop\" -ForegroundColor Green
