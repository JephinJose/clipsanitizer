# ClipSanitizer

A tiny, open-source tray app for Windows and macOS that automatically
scrubs invisible/tracking characters from text as soon as you copy it.

It removes:
- Zero-width spaces/joiners (`U+200B`–`U+200F`, `U+2060`–`U+2064`, `U+FEFF`)
- Bidi override/isolate control characters (used to hide or reorder text)
- Unicode tag characters (`U+E0000`–`U+E007F`) — a known steganographic
  channel used to embed hidden identifiers in plain-looking text
- Variation selectors and stray control characters

Normal punctuation, emoji, accented characters, tabs, and newlines are left
untouched.

## How it works

A background thread polls the system clipboard every 0.5s. When it detects
new text, it runs the sanitizer and writes the cleaned version back to the
clipboard — so anything you paste is already scrubbed. A tray icon lets you
toggle it on/off and see how many items were cleaned this session.

## Install

```bash
git clone <this-repo>
cd clipsanitizer
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### macOS notes
The first time it accesses the clipboard/tray, macOS may prompt for
Accessibility or Automation permission — grant it in
System Settings → Privacy & Security.

### Windows notes
Runs as-is with the standard Python installer. To run it silently in the
background without a console window, use `pythonw main.py`.

### Run at login (optional)
- **macOS**: add a Login Item pointing at a small shell script that
  activates the venv and runs `python main.py`.
- **Windows**: place a shortcut to `pythonw main.py` in
  `shell:startup`.

## Packaging as a standalone app (optional)

Use [PyInstaller](https://pyinstaller.org) to produce a double-clickable app
with no Python install required:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name ClipSanitizer main.py
```

## Tests

```bash
pip install pytest
pytest
```

## License

MIT — see [LICENSE](LICENSE).
