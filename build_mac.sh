#!/bin/bash
# Builds dist/ClipSanitizer.app: a double-clickable macOS app with Python,
# Tk, and all dependencies bundled in. End users need nothing installed.
#
# Building it requires a Python with working Tk (many system/pyenv builds
# don't have this). Easiest path on macOS:
#   brew install python-tk@3.13
#   ./build_mac.sh /opt/homebrew/bin/python3.13
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

PYTHON="${1:-python3}"
"$PYTHON" -c "import tkinter" || {
  echo "error: $PYTHON has no Tk support. Install one that does, e.g.:" >&2
  echo "  brew install python-tk@3.13 && ./build_mac.sh /opt/homebrew/bin/python3.13" >&2
  exit 1
}

"$PYTHON" -m venv build_venv
source build_venv/bin/activate
pip install -q -r requirements.txt pyinstaller
rm -rf build dist
pyinstaller ClipSanitizer.spec --noconfirm
deactivate

echo "Built: dist/ClipSanitizer.app"
