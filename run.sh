#!/bin/bash
# Launches ClipSanitizer using its venv. Point a macOS Login Item at this file.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR" || exit 1
source venv/bin/activate
exec python main.py
