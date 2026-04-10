@echo off
setlocal
cd /d %~dp0

if not exist .venv (
  py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -U pip
python -m pip install -r requirements-packaging.txt
python build_desktop.py

echo.
echo Build finished. Output is under dist\VideoKBDesktop\
endlocal
