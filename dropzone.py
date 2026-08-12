"""Popover-style file cleaner: click (or, where available, drag a file) to
get a metadata-scrubbed copy written next to the original. Runs as its own
process (launched from the tray menu) so its GUI loop never competes with
pystray's for the main thread. Anchored under the menu bar and auto-dismisses
on focus loss so it reads as part of the tray icon rather than a stray window.

Drag-and-drop uses tkinterdnd2, which bundles a native tkdnd library built
against a specific Tcl/Tk release; on a mismatched Tcl/Tk (e.g. Homebrew's
Tcl 9 vs. tkdnd's Tcl 8.6 binary) it fails to load. That failure is caught
here and the window falls back to a plain "Choose File..." button, which
uses only Tk's built-in file dialog and always works."""
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from filemeta import clean_file

WIDTH, HEIGHT = 300, 210
MARGIN_TOP = 30   # clears the macOS menu bar
MARGIN_RIGHT = 20
BG = "#1e1e1e"
BORDER = "#3a3a3a"
ACCENT = "#4da3ff"
FG = "#e8e8e8"
FG_DIM = "#9a9a9a"

IDLE_TEXT_DND = "Drag a file here"
IDLE_TEXT_CLICK = "Click to choose a file"
IDLE_SUBTEXT = "Images, PDFs, Word/Excel/PowerPoint"


def try_load_dnd(tk_root_cls):
    """Return (TkClass, dnd_ok). Falls back to plain tkinter.Tk on any
    failure to load the native drag-and-drop library."""
    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD
        root = TkinterDnD.Tk()
        return root, DND_FILES
    except Exception:
        return tk_root_cls(), None


def parse_dropped_paths(data: str):
    # Tk gives space-joined paths, {}-wrapped when they contain spaces.
    paths, buf, in_brace = [], "", False
    for ch in data:
        if ch == "{":
            in_brace = True
        elif ch == "}":
            in_brace = False
        elif ch == " " and not in_brace:
            if buf:
                paths.append(buf)
                buf = ""
        else:
            buf += ch
    if buf:
        paths.append(buf)
    return paths


class DropZone:
    def __init__(self):
        self.root, self.dnd_files_const = try_load_dnd(tk.Tk)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self._position_top_right()
        self.root.configure(bg=BORDER)

        outer = tk.Frame(self.root, bg=BORDER)
        outer.pack(fill="both", expand=True)
        card = tk.Frame(outer, bg=BG)
        card.pack(fill="both", expand=True, padx=1, pady=1)

        header = tk.Frame(card, bg=BG)
        header.pack(fill="x", padx=16, pady=(14, 4))
        self.badge = tk.Canvas(header, width=18, height=18, bg=BG, highlightthickness=0)
        self.badge.create_oval(2, 2, 16, 16, fill=ACCENT, outline="")
        self.badge.pack(side="left")
        tk.Label(
            header, text="Clean Files", font=("Helvetica", 13, "bold"),
            fg=FG, bg=BG,
        ).pack(side="left", padx=(8, 0))

        idle_text = IDLE_TEXT_DND if self.dnd_files_const else IDLE_TEXT_CLICK
        self.dropzone = tk.Frame(
            card, bg="#262626", highlightbackground="#454545",
            highlightthickness=1, cursor="hand2" if not self.dnd_files_const else "",
        )
        self.dropzone.pack(fill="both", expand=True, padx=16, pady=(6, 12))

        self.title_label = tk.Label(
            self.dropzone, text=idle_text, font=("Helvetica", 13),
            fg=FG, bg="#262626", justify="center",
        )
        self.title_label.pack(expand=True, pady=(0, 2))
        self.sub_label = tk.Label(
            self.dropzone, text=IDLE_SUBTEXT, font=("Helvetica", 10),
            fg=FG_DIM, bg="#262626", justify="center", wraplength=WIDTH - 60,
        )
        self.sub_label.pack()

        self.idle_text = idle_text

        if self.dnd_files_const:
            for widget in (self.dropzone, self.title_label, self.sub_label):
                widget.drop_target_register(self.dnd_files_const)
                widget.dnd_bind("<<Drop>>", self._on_drop)
        else:
            for widget in (self.dropzone, self.title_label, self.sub_label):
                widget.bind("<Button-1>", self._on_click_choose)

        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.root.bind("<FocusOut>", self._on_focus_out)
        self.root.after(150, lambda: self.root.focus_force())

    def _position_top_right(self):
        screen_w = self.root.winfo_screenwidth()
        x = screen_w - WIDTH - MARGIN_RIGHT
        self.root.geometry(f"{WIDTH}x{HEIGHT}+{x}+{MARGIN_TOP}")

    def _on_focus_out(self, event):
        # Ignore spurious FocusOut while the window is still settling in.
        self.root.after(200, self._close_if_unfocused)

    def _close_if_unfocused(self):
        if not self.root.focus_displayof():
            self.root.destroy()

    def _on_click_choose(self, event):
        paths = filedialog.askopenfilenames(title="Choose files to clean")
        if paths:
            self._process(paths)

    def _on_drop(self, event):
        self._process(parse_dropped_paths(event.data))

    def _process(self, paths):
        lines = []
        for p in paths:
            try:
                out = clean_file(p)
                lines.append(f"✓ {out.name}")
            except Exception:
                lines.append(f"✗ {Path(p).name}")
        self.title_label.config(text="\n".join(lines) if lines else "No files detected")
        self.sub_label.config(text="Cleaned copy saved next to the original")
        self.root.after(3500, self._reset)

    def _reset(self):
        self.title_label.config(text=self.idle_text)
        self.sub_label.config(text=IDLE_SUBTEXT)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    DropZone().run()
