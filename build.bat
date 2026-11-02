@echo off
rem Build dist\ClaudeMascot.exe (single file, images bundled inside).
rem Requires: Python 3.13+, pip install pyinstaller pystray pillow
rem mascot\version.txt (release workflow writes the tag) goes inside too; without it the exe skips update checks.
cd /d "%~dp0"
set VERSION_DATA=
if exist mascot\version.txt set VERSION_DATA=--add-data "mascot\version.txt;."
python -m PyInstaller --noconfirm --onefile --windowed --name ClaudeMascot --icon mascot\icon.ico --add-data "mascot\images;images" %VERSION_DATA% mascot\claude_mascot.pyw
