# clipsanitizer

**the missing step between "AI generated this" and "I'm pasting this
anywhere else."**

Text out of an LLM chat window isn't always just text. Some providers and
sites embed invisible Unicode into generated output — zero-width
characters and Unicode "tag" sequences used as a hidden watermark or
fingerprint of that specific copy — and it's undetectable to the eye,
survives a normal copy-paste, and stays in whatever you send, publish, or
submit next. clipsanitizer sits quietly in your tray and strips it the
instant you copy, from anything: an AI chat, a doc, a web page. No
accounts, no network calls, nothing leaves your machine.

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-lightgrey.svg)](#install)

```
$ python3 -c "import pyperclip; pyperclip.copy('hel​o wor‌ld﻿')"
$ python3 -c "import pyperclip; print(repr(pyperclip.paste()))"
'hello world'
```

## why

Copying "AI generated" text and pasting it somewhere else — an email, a
doc, a form, someone else's editor — is now one of the most common
copy-paste flows there is, and it's the one most likely to carry
something you didn't put there. Invisible zero-width characters and
bidi-control codes can be used to fingerprint a specific generation or
reorder/hide substrings; Unicode "tag" characters are a known covert
channel for embedding a hidden payload right alongside the visible words.
None of it renders, none of it shows up in a normal read-through — it
just rides along. clipsanitizer strips all of it the moment it hits your
clipboard, whether the text came from an AI tool, a web page, a PDF, or a
chat app, so what you paste is exactly and only what you saw.

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

Text isn't the only thing that carries hidden identifiers. Generated
images and exported documents carry their own metadata trail: EXIF
(generation tool, timestamps, sometimes GPS if it round-tripped through
another app), a PDF's Info dict and XMP, or an Office file's
author/company properties. Open the drop-zone window from the tray menu
(**Clean Files...**) and drag a file onto it. It writes a scrubbed copy
next to the original, named `photo.clean.jpg`, `report.clean.pdf`, etc. —
nothing is overwritten in place.

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
