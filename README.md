# clipsanitizer

A small tray app for Mac and Windows that cleans your clipboard and your
files. No accounts, no network calls. Nothing leaves your machine.

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-lightgrey.svg)](#install)

## Why this exists

Text copied from an AI chat, a web page, or a document is not always
just text. It can carry invisible characters you never see: zero-width
spaces, bidi control codes, and Unicode "tag" characters. Some AI
providers and websites use these to fingerprint or watermark a specific
copy of text. They render as nothing, but they survive a normal
copy-paste and travel with you into whatever you send, publish, or
submit next.

clipsanitizer watches your clipboard in the background and strips these
characters the moment you copy something, so what you paste is exactly
what you saw and nothing more.

```
$ python3 -c "import pyperclip; pyperclip.copy('hel​o wor‌ld﻿')"
$ python3 -c "import pyperclip; print(repr(pyperclip.paste()))"
'hello world'
```

## What gets removed from text

| Category | Examples |
|---|---|
| Zero-width formatting | `U+200B`–`U+200F`, `U+2060`–`U+2064`, `U+FEFF` |
| Bidi control characters | embedding/override (`U+202A`–`U+202E`), isolates (`U+2066`–`U+2069`) |
| Unicode tag characters | `U+E0000`–`U+E007F`, a known channel for hiding data |
| Variation selectors | `U+FE00`–`U+FE0F` |
| Stray control bytes | non-printing ASCII control characters |

Normal punctuation, accents, emoji, tabs, and newlines are left alone.

## Cleaning file metadata

Hidden identifiers show up in files too. Photos carry EXIF data (camera,
timestamps, sometimes location). PDFs carry an Info dictionary and XMP
metadata. Office files carry author and company properties.

Open the **Clean Files...** window from the tray menu and drop a file
onto it. It saves a cleaned copy next to the original, for example
`photo.clean.jpg` or `report.clean.pdf`. Your original file is never
touched.

| File type | What gets stripped |
|---|---|
| Images (jpg, png, tiff, webp, bmp) | all EXIF/IPTC metadata |
| PDF | the Info dictionary and XMP metadata |
| Office (docx, xlsx, pptx) | author, company, and edit history properties |
| Anything else | copied through unchanged |

If drag-and-drop doesn't work on your system, the window falls back to a
plain "Choose File..." button automatically. Either way, file cleaning
still works.

## Install

### Option A: download the app (recommended)

No Python or terminal needed.

- **macOS**: download [`ClipSanitizer.app`](../../releases/latest), unzip
  it, and drag it into Applications. On first launch, macOS may ask for
  Accessibility or Automation permission. Grant it in System Settings
  under Privacy & Security.
- **Windows**: download [`ClipSanitizer.exe`](../../releases/latest) and
  run it. Windows SmartScreen may warn that the app is unsigned. Click
  "More info" and then "Run anyway."

A small icon appears in your tray or menu bar. A solid dot means the app
is active, a ring means it's paused. Click it to see how many items were
cleaned this session, toggle it on or off, or open **Clean Files...**.

### Option B: run from source

```bash
git clone git@github.com:JephinJose/clipsanitizer.git
cd clipsanitizer
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py             # Windows: pythonw main.py, to skip the console window
```

The file-cleaner window needs a Python build with Tk support. Check with
`python3 -c "import tkinter"`. The official installers from python.org
include this. Some pyenv builds don't, unless Tcl/Tk was installed
first.

### Run at login

If you installed the packaged app, just add it as a Login Item (macOS)
or drop it in the Startup folder (Windows). No extra steps needed.

If you're running from source:

- **macOS**: System Settings → General → Login Items, then add
  [`run.sh`](run.sh). It activates the virtual environment and runs the
  app for you. Make it executable first with `chmod +x run.sh`.
- **Windows**: create a shortcut pointing to
  `pythonw.exe C:\path\to\clipsanitizer\main.py` and place it in
  `shell:startup`.

### Building the app yourself

```bash
# macOS, needs a Tk-enabled Python
brew install python-tk@3.13
./build_mac.sh /opt/homebrew/bin/python3.13

# Windows, from a standard python.org install
build_win.bat
```

## Tests

```bash
pip install pytest
pytest
```

## License

MIT. See [LICENSE](LICENSE).
