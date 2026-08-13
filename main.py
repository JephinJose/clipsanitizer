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


def hide_dock_icon():
    # The packaged .app suppresses its Dock icon via LSUIElement in
    # Info.plist, but that key only takes effect when macOS launches the
    # .app bundle itself. Running from source (`python main.py`) has no such
    # Info.plist, so pystray's status icon defaults to a regular, foreground
    # app: a bouncing Python Dock icon and a Cmd+Tab entry, exactly what a
    # background-only tray app shouldn't have. Setting the activation policy
    # here fixes that regardless of how the process was started.
    #
    # This is the pystray/tray-icon copy, safe to call before any window
    # exists since pystray uses AppKit directly. dropzone.py has its own
    # copy with a stricter ordering requirement -- see the note there.
    if platform.system() != "Darwin":
        return
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
        NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    except Exception:
        pass


def _tray_icon_anchor(icon):
    # Screen point just below the tray icon, in Tk's top-left-origin,
    # y-grows-downward coordinate system (what Tk's .geometry() expects) --
    # or None if it can't be determined, so the caller can fall back to a
    # fixed corner. pystray has no public cross-platform API for this, so
    # on macOS we reach into its private NSStatusItem (icon._status_item)
    # for the button's actual screen frame, which is in Cocoa's
    # bottom-left-origin, y-grows-upward system and needs converting.
    if platform.system() != "Darwin":
        return None
    try:
        from AppKit import NSScreen
        frame = icon._status_item.button().window().frame()
        screen_h = NSScreen.mainScreen().frame().size.height
        x = frame.origin.x + frame.size.width / 2
        y = screen_h - frame.origin.y
        return (x, y)
    except Exception:
        return None


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
        self.dropzone_proc = None
        self.about_proc = None

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

    def _open_popover(self, icon, flag, proc_attr, failure_message):
        # Both the drop-zone and the About window are small Tk popovers
        # launched as their own subprocess (see dropzone.py's module
        # docstring for why), spawned and supervised the same way: dedupe
        # against a still-running previous instance, re-invoke this same
        # executable with a flag rather than pointing at the target script
        # directly so a PyInstaller-frozen build (which has no loose .py
        # files at runtime) can spawn it as a subprocess of itself, and
        # report a notification if it fails to come up at all.
        if getattr(self, proc_attr) is not None and getattr(self, proc_attr).poll() is None:
            return
        if getattr(sys, "frozen", False):
            args = [sys.executable, flag]
        else:
            args = [sys.executable, str(Path(__file__).resolve()), flag]
        anchor = _tray_icon_anchor(icon)
        if anchor is not None:
            args += ["--anchor", str(anchor[0]), str(anchor[1])]
        proc = subprocess.Popen(args, stderr=subprocess.PIPE)
        setattr(self, proc_attr, proc)
        threading.Thread(
            target=self._watch_popover_startup, args=(icon, proc, failure_message), daemon=True,
        ).start()

    def _watch_popover_startup(self, icon, proc, failure_message):
        # If the window fails to come up at all (e.g. this Python build has
        # no Tk support), the subprocess exits almost immediately. A running
        # popover sits in its event loop, so a timeout here means success.
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            return
        if proc.returncode != 0 and Icon.HAS_NOTIFICATION:
            icon.notify(failure_message, "ClipSanitizer")

    def _open_dropzone(self, icon, item):
        self._open_popover(
            icon, "--dropzone", "dropzone_proc",
            "Clean Files window couldn't start. This Python build may be missing Tk support.",
        )

    def _show_about(self, icon, item):
        self._open_popover(
            icon, "--about", "about_proc",
            "About window couldn't start. This Python build may be missing Tk support.",
        )

    def _quit(self, icon, item):
        # The drop-zone and About window run as their own subprocesses (see
        # _open_popover), so quitting the tray icon doesn't touch them by
        # default -- they'd be left running, windows still on screen, as
        # orphans with no tray icon left to reopen or account for them.
        for proc in (self.dropzone_proc, self.about_proc):
            if proc is not None and proc.poll() is None:
                proc.terminate()
        icon.stop()

    def run(self):
        threading.Thread(target=self._watch_clipboard, daemon=True).start()
        menu = Menu(
            MenuItem("About ClipSanitizer", self._show_about),
            MenuItem("Clean Files...", self._open_dropzone, default=True),
            MenuItem(self._status_text, None, enabled=False),
            MenuItem("Enabled", self._toggle, checked=lambda item: self.enabled),
            MenuItem("Quit", self._quit),
        )
        icon = Icon("ClipSanitizer", self._make_icon_image(), "ClipSanitizer", menu)
        threading.Thread(target=self._watch_theme, args=(icon,), daemon=True).start()
        icon.run()


if __name__ == "__main__":
    # dropzone.py and about.py hide their own Dock icon once their Tk root
    # exists -- see the ordering note on hide_dock_icon() above.
    if "--dropzone" in sys.argv:
        from dropzone import DropZone
        DropZone().run()
    elif "--about" in sys.argv:
        from about import AboutWindow
        AboutWindow().run()
    else:
        hide_dock_icon()
        ClipSanitizer().run()
