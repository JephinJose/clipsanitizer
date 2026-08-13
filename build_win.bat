@echo off
REM Builds dist\ClipSanitizer\ClipSanitizer.exe: a double-clickable Windows
REM app with Python, Tk, and all dependencies bundled in. End users need
REM nothing installed. Run this from a Python install that includes Tk
REM (the standard python.org installer does, by default).
python -c "import tkinter" || (echo error: this Python has no Tk support & exit /b 1)

python -m venv build_venv
call build_venv\Scripts\activate.bat
pip install -q -r requirements.txt pyinstaller
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
pyinstaller --noconfirm --windowed --name ClipSanitizer --hidden-import dropzone --hidden-import about --hidden-import popover --hidden-import filemeta --hidden-import sanitize main.py
call build_venv\Scripts\deactivate.bat

echo Built: dist\ClipSanitizer\ClipSanitizer.exe
