@echo off
rem Build dist\ClaudeMascot.exe (single file, images bundled inside).
rem Requires: Python 3.13+, pip install pyinstaller pystray pillow
cd /d "%~dp0"
python -m PyInstaller --noconfirm --onefile --windowed --name ClaudeMascot --icon mascot\icon.ico --add-data "mascot\images;images" mascot\claude_mascot.pyw
