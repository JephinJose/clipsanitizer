"""Shared plumbing for small, borderless windows meant to read as part of
the tray icon rather than independent windows -- the drop-zone and the
About window both run as their own subprocess (see dropzone.py's module
docstring for why) and both need the same treatment: no Dock presence,
positioned just under wherever the tray icon actually is, can't be
minimized, and dismiss themselves on Escape, focus loss, or an attempt to
minimize."""
import platform
import sys
import tkinter as tk

MARGIN_TOP = 30   # clears the macOS menu bar, used when no --anchor is given
MARGIN_RIGHT = 20
ANCHOR_GAP = 4    # breathing room between the tray icon and the window

BG = "#1e1e1e"
BORDER = "#3a3a3a"
ACCENT = "#4da3ff"
FG = "#e8e8e8"
FG_DIM = "#9a9a9a"


def anchor_from_argv():
    # main.py passes `--anchor X Y` (screen point just below the tray icon,
    # Tk-style top-left-origin coordinates) when it can determine one.
    # Falls back to None -- a fixed corner -- when run standalone, or on a
    # platform/backend where main.py couldn't locate the icon.
    if "--anchor" not in sys.argv:
        return None
    i = sys.argv.index("--anchor")
    try:
        return float(sys.argv[i + 1]), float(sys.argv[i + 2])
    except (IndexError, ValueError):
        return None


def hide_dock_icon():
    # Without this, this window runs as a regular foreground app: a
    # bouncing Python Dock icon and a Cmd+Tab entry for what's meant to be a
    # transient popover anchored to the tray icon. The packaged .app avoids
    # this via LSUIElement in Info.plist, but that only applies when macOS
    # launches the .app bundle itself, not when this file runs as a
    # subprocess re-invoking the frozen executable (or as plain `python
    # main.py --dropzone` from source) -- so it's set at runtime instead.
    #
    # Must run AFTER the Tk root already exists. Tk's own Cocoa init
    # expects to be the first thing to touch NSApplication and installs a
    # custom subclass with extra selectors (e.g. -macOSVersion); grabbing
    # NSApplication.sharedApplication() via AppKit first hands Tk a plain
    # NSApplication instead, and Tk crashes hard the moment it calls one of
    # those selectors.
    #
    # Duplicated from main.py rather than imported: the frozen build's
    # hiddenimports (ClipSanitizer.spec, build_win.bat) don't include "main"
    # since PyInstaller treats the entry-point script as the bootstrap, not
    # an importable module, so `from main import ...` would break the
    # packaged app even though it works fine from source.
    if platform.system() != "Darwin":
        return
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
        NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    except Exception:
        pass


def disable_minimize(root):
    # overrideredirect blocks Tk's own `wm iconify`, but macOS's native
    # Cmd+M still miniaturizes the window regardless -- that shortcut is a
    # menu key equivalent wired straight to Cocoa's performMiniaturize:,
    # bypassing Tk's window-manager protocol layer entirely. Clearing the
    # miniaturizable bit on the real NSWindow stops that at the source
    # (verified directly: calling performMiniaturize_ on the window is a
    # no-op once this bit is cleared), rather than reacting after the fact
    # via Popover's <Unmap> handler, which is kept as a fallback for any
    # other path that might still unmap the window.
    #
    # Must run after the window has been mapped at least once (Tk's root
    # only shows up in NSApp.windows() once realized), and there's no
    # public Tk API for the underlying NSWindow, so this finds it the same
    # way as any other window enumeration: the one visible window among
    # this single-window process's NSApp.windows().
    if platform.system() != "Darwin":
        return
    try:
        from AppKit import NSApp
        MINIATURIZABLE = 1 << 2  # NSWindowStyleMaskMiniaturizable
        for w in NSApp.windows():
            if w.isVisible():
                w.setStyleMask_(w.styleMask() & ~MINIATURIZABLE)
                break
    except Exception:
        pass


class Popover:
    """Base for a small, borderless window anchored under the tray icon.

    Subclasses must create and assign `self.root` (a Tk root) before
    calling `super().__init__()`, build their widgets, then call
    `self._finish_setup(width, height)` once those widgets are packed.
    """

    def __init__(self):
        self._closing = False
        hide_dock_icon()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

    def _finish_setup(self, width, height):
        self._width = width
        self._height = height
        # Packing widgets gives the window its natural size, which Tk uses
        # to silently override any position set earlier -- so the explicit
        # position has to be (re-)applied last, once layout has settled, or
        # it gets discarded the moment the window is realized.
        self.root.update_idletasks()
        self._position_window()
        disable_minimize(self.root)
        self.root.bind("<Escape>", lambda e: self._dismiss())
        self.root.bind("<FocusOut>", self._on_focus_out)
        self.root.bind("<Unmap>", self._on_unmap)
        self.root.after(150, lambda: self.root.focus_force())

    def _position_window(self):
        screen_w = self.root.winfo_screenwidth()
        anchor = anchor_from_argv()
        if anchor is not None:
            anchor_x, anchor_y = anchor
            x = int(anchor_x - self._width / 2)
            y = int(anchor_y + ANCHOR_GAP)
        else:
            x = screen_w - self._width - MARGIN_RIGHT
            y = MARGIN_TOP
        x = max(0, min(x, screen_w - self._width))  # keep it fully on-screen
        self.root.geometry(f"{self._width}x{self._height}+{x}+{y}")

    def _dismiss(self):
        # The single synchronous path every "close this window" trigger
        # (Escape, focus loss) funnels through, so a destroy is only ever
        # attempted once no matter how many of those fire. _on_unmap below
        # guards the same way but separately, since it needs to defer the
        # actual destroy.
        if self._closing:
            return
        self._closing = True
        self._destroy_now()

    def _destroy_now(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def _on_unmap(self, event):
        # overrideredirect blocks Tk's own `wm iconify` ("can't iconify:
        # override-redirect flag is set"), but macOS's native Cmd+M still
        # minimizes the underlying window regardless, since that shortcut
        # goes straight to Cocoa rather than through Tk's window-manager
        # protocol layer -- disable_minimize() blocks that directly, but
        # this stays as a fallback for any other path that might still
        # unmap the window. A minimized instance has no tray icon pointing
        # back at it and no normal way to restore it, so it's effectively a
        # leak -- treat becoming unmapped the same as a dismiss, matching
        # this window's whole point of being a transient popover rather
        # than a real, independently-lived window.
        #
        # The destroy itself is deferred: doing it synchronously, from
        # inside the callback for the very state transition that's tearing
        # the window down, crashes the process outright (a hard segfault,
        # not a catchable TclError) instead of unwinding cleanly. But
        # _closing is set right here, synchronously -- a single minimize
        # can fire several Unmap events before the deferred callback below
        # ever runs, and without this, each one would schedule its own
        # doomed attempt to destroy an already-gone window, which raises
        # "invalid command name" once the first one actually completes.
        if self._closing:
            return
        self._closing = True
        self.root.after_idle(self._destroy_now)

    def _on_focus_out(self, event):
        # Ignore spurious FocusOut while the window is still settling in.
        self.root.after(200, self._close_if_unfocused)

    def _close_if_unfocused(self):
        try:
            if not self.root.focus_displayof():
                self._dismiss()
        except tk.TclError:
            pass  # window already closed (e.g. via Escape) before this timer fired

    def run(self):
        self.root.mainloop()
