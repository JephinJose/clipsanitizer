"""Popover-style About window: what ClipSanitizer does and confirms nothing
leaves the machine. Runs as its own process for the same reasons as
dropzone.py -- see its module docstring."""
import tkinter as tk

from popover import BG, FG, FG_DIM, ACCENT, BORDER, Popover

WIDTH, HEIGHT = 300, 160

DESCRIPTION = (
    "Cleans invisible tracking characters from your clipboard and strips "
    "identifying metadata from your files."
)
PRIVACY_NOTE = "No accounts, no network calls. Nothing leaves your machine."


class AboutWindow(Popover):
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ClipSanitizer - About")
        super().__init__()
        self.root.configure(bg=BORDER)

        outer = tk.Frame(self.root, bg=BORDER)
        outer.pack(fill="both", expand=True)
        card = tk.Frame(outer, bg=BG)
        card.pack(fill="both", expand=True, padx=1, pady=1)

        header = tk.Frame(card, bg=BG)
        header.pack(fill="x", padx=16, pady=(14, 4))
        badge = tk.Canvas(header, width=18, height=18, bg=BG, highlightthickness=0)
        badge.create_oval(2, 2, 16, 16, fill=ACCENT, outline="")
        badge.pack(side="left")
        tk.Label(
            header, text="ClipSanitizer", font=("Helvetica", 13, "bold"),
            fg=FG, bg=BG,
        ).pack(side="left", padx=(8, 0))

        body = tk.Frame(card, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=(6, 14))
        tk.Label(
            body, text=DESCRIPTION, font=("Helvetica", 11),
            fg=FG, bg=BG, justify="left", wraplength=WIDTH - 32,
        ).pack(anchor="w")
        tk.Label(
            body, text=PRIVACY_NOTE, font=("Helvetica", 10),
            fg=FG_DIM, bg=BG, justify="left", wraplength=WIDTH - 32,
        ).pack(anchor="w", pady=(10, 0))

        self._finish_setup(WIDTH, HEIGHT)


if __name__ == "__main__":
    AboutWindow().run()
