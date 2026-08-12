# clipsanitizer

**what you copy shouldn't carry a passenger.**

Every clipboard event gets scanned and scrubbed of invisible characters
before you paste it anywhere — zero-width spaces, bidi overrides, Unicode
tag characters, stray control bytes. One small tray app, no accounts, no
network calls, nothing leaves your machine.

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-lightgrey.svg)](#install)

```
$ python3 -c "import pyperclip; pyperclip.copy('hel​o wor‌ld﻿')"
$ python3 -c "import pyperclip; print(repr(pyperclip.paste()))"
'hello world'
```

## why

Text copied from a web page, PDF, or chat app can carry characters you
never see: zero-width joiners used to fingerprint a specific copy, bidi
control codes that reorder or hide substrings, Unicode "tag" characters
that smuggle a hidden payload alongside visible text. clipsanitizer
strips all of it the moment it hits your clipboard, so what you paste is
exactly what you saw.

## what it removes

| category | examples |
|---|---|
| zero-width formatting | `U+200B`–`U+200F`, `U+2060`–`U+2064`, `U+FEFF` |
| bidi control | embedding/override (`U+202A`–`U+202E`), isolates (`U+2066`–`U+2069`) |
| Unicode tag characters | `U+E0000`–`U+E007F` (steganographic channel) |
| variation selectors | `U+FE00`–`U+FE0F` |
| stray control bytes | non-printing ASCII control chars |

Normal punctuation, accents, emoji, tabs, and newlines are left alone.

## cleaning file metadata

Text isn't the only thing that carries hidden identifiers — photos embed
EXIF (camera, GPS, timestamps), PDFs embed an Info dict and XMP, and
Office files embed author/company properties. Open the drop-zone window
from the tray menu (**Clean Files...**) and drag a file onto it. It writes
a scrubbed copy next to the original, named `photo.clean.jpg`,
`report.clean.pdf`, etc. — nothing is overwritten in place.

| type | what's stripped |
|---|---|
| images (jpg, png, tiff, webp, bmp) | all EXIF/IPTC metadata (re-encodes pixel data only) |
| PDF | `/Info` dictionary and XMP metadata |
| Office (docx, xlsx, pptx) | `docProps/core.xml`, `app.xml`, `custom.xml` (author, company, edit history) |
| anything else | copied through unchanged |

The drop-zone tries drag-and-drop first; if the native drag-and-drop
library can't load on your system (a known issue when it was built
against a different Tcl/Tk than your Python has), it falls back
automatically to a plain "Choose File..." button — either way, nothing
crashes and cleaning still works.

## install

### option A: packaged app (recommended)

No Python, no terminal, no dependencies — download and run:

- **macOS**: [`ClipSanitizer.app`](../../releases/latest) — unzip, drag to
  Applications, open it. First run may prompt for Accessibility/Automation
  permission in System Settings → Privacy & Security.
- **Windows**: [`ClipSanitizer.exe`](../../releases/latest) — unzip and
  run it. Windows SmartScreen may warn about an unsigned app on first
  launch; click "More info" → "Run anyway".

A tray/menu-bar icon appears: solid dot = active, ring = paused. Click
it for a running count of items cleaned this session, to toggle on/off,
or to open **Clean Files...** for the file-metadata cleaner.

### option B: run from source

```bash
git clone git@github.com:JephinJose/clipsanitizer.git
cd clipsanitizer
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py             # Windows: pythonw main.py (no console window)
```

Needs a Python with Tk support for the file-cleaner window
(`python3 -c "import tkinter"`) — the official python.org installers
include it; some pyenv builds don't unless Tcl/Tk was installed first.

### run at login (source install only)
- **macOS** — System Settings → General → Login Items → add
  [`run.sh`](run.sh) (it `cd`s into the repo, activates the venv, and runs
  `python main.py`). Make sure it's executable: `chmod +x run.sh`.
- **Windows** — create a shortcut with target
  `pythonw.exe C:\path\to\clipsanitizer\main.py` and drop it in `shell:startup`.

(The packaged app can just be added directly as a Login Item / put in
the Windows Startup folder — no script needed.)

### building the packaged app yourself

```bash
# macOS — needs a Tk-enabled Python, e.g.:
brew install python-tk@3.13
./build_mac.sh /opt/homebrew/bin/python3.13

# Windows — from a python.org install (has Tk by default):
build_win.bat
```

## tests

```bash
pip install pytest
pytest
```

## license

MIT — see [LICENSE](LICENSE).
