"""ClipSanitizer: background tray app that scrubs invisible/tracking
characters from clipboard text as soon as you copy it. Windows + macOS."""
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path

import pyperclip
from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem

from sanitize import sanitize

POLL_INTERVAL = 0.5
THEME_POLL_INTERVAL = 2.0

LIGHT_DOT = (20, 20, 20, 255)   # dark dot for a light menu bar
DARK_DOT = (235, 235, 235, 255)  # light dot for a dark menu bar


def is_dark_mode() -> bool:
    system = platform.system()
    try:
        if system == "Darwin":
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True, timeout=1,
            )
            return result.stdout.strip() == "Dark"
        if system == "Windows":
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return value == 0
    except Exception:
        pass
    return False


class ClipSanitizer:
    def __init__(self):
        self.enabled = True
        self.last_seen = ""
        self.cleaned_count = 0
        self.dark_mode = is_dark_mode()

    def _make_icon_image(self):
        # Minimal glyph: a single dot, hollow when paused, colored for contrast.
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        color = DARK_DOT if self.dark_mode else LIGHT_DOT
        if self.enabled:
            d.ellipse([10, 10, 54, 54], fill=color)
        else:
            d.ellipse([10, 10, 54, 54], outline=color, width=5)
        return img

    def _watch_theme(self, icon):
        while True:
            time.sleep(THEME_POLL_INTERVAL)
            current = is_dark_mode()
            if current != self.dark_mode:
                self.dark_mode = current
                icon.icon = self._make_icon_image()

    def _watch_clipboard(self):
        try:
            self.last_seen = pyperclip.paste()
        except Exception:
            self.last_seen = ""
        while True:
            time.sleep(POLL_INTERVAL)
            if not self.enabled:
                continue
            try:
                current = pyperclip.paste()
            except Exception:
                continue
            if current == self.last_seen:
                continue
            cleaned = sanitize(current)
            if cleaned != current:
                pyperclip.copy(cleaned)
                self.cleaned_count += 1
                self.last_seen = cleaned
            else:
                self.last_seen = current

    def _toggle(self, icon, item):
        self.enabled = not self.enabled
        icon.icon = self._make_icon_image()

    def _status_text(self, item):
        return f"Cleaned {self.cleaned_count} item(s) this session"

    def _open_dropzone(self, icon, item):
        # Re-invoke this same executable with a flag rather than pointing at
        # dropzone.py directly, so a PyInstaller-frozen build (which has no
        # loose .py files at runtime) can spawn the drop-zone as a subprocess
        # of itself.
        if getattr(sys, "frozen", False):
            args = [sys.executable, "--dropzone"]
        else:
            args = [sys.executable, str(Path(__file__).resolve()), "--dropzone"]
        subprocess.Popen(args)

    def run(self):
        threading.Thread(target=self._watch_clipboard, daemon=True).start()
        menu = Menu(
            MenuItem("Clean Files...", self._open_dropzone, default=True),
            MenuItem(self._status_text, None, enabled=False),
            MenuItem("Enabled", self._toggle, checked=lambda item: self.enabled),
            MenuItem("Quit", lambda icon, item: icon.stop()),
        )
        icon = Icon("ClipSanitizer", self._make_icon_image(), "ClipSanitizer", menu)
        threading.Thread(target=self._watch_theme, args=(icon,), daemon=True).start()
        icon.run()


if __name__ == "__main__":
    if "--dropzone" in sys.argv:
        from dropzone import DropZone
        DropZone().run()
    else:
        ClipSanitizer().run()
