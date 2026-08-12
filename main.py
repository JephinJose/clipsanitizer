"""ClipSanitizer: background tray app that scrubs invisible/tracking
characters from clipboard text as soon as you copy it. Windows + macOS."""
import threading
import time

import pyperclip
from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem

from sanitize import sanitize

POLL_INTERVAL = 0.5


class ClipSanitizer:
    def __init__(self):
        self.enabled = True
        self.last_seen = ""
        self.cleaned_count = 0

    def _make_icon_image(self):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        color = (46, 160, 67, 255) if self.enabled else (140, 140, 140, 255)
        d.rounded_rectangle([8, 4, 56, 60], radius=10, outline=color, width=5)
        d.rectangle([20, 0, 44, 10], fill=color)
        if self.enabled:
            d.line([18, 32, 28, 44], fill=color, width=6)
            d.line([28, 44, 48, 20], fill=color, width=6)
        return img

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

    def run(self):
        threading.Thread(target=self._watch_clipboard, daemon=True).start()
        menu = Menu(
            MenuItem(self._status_text, None, enabled=False),
            MenuItem("Enabled", self._toggle, checked=lambda item: self.enabled),
            MenuItem("Quit", lambda icon, item: icon.stop()),
        )
        icon = Icon("ClipSanitizer", self._make_icon_image(), "ClipSanitizer", menu)
        icon.run()


if __name__ == "__main__":
    ClipSanitizer().run()
