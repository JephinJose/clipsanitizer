"""Core sanitization: strip characters used to fingerprint or hide tracking
data in copied text (zero-width chars, bidi overrides, variation selectors,
Unicode tag characters), without touching normal punctuation/whitespace."""
import re
import unicodedata

# Explicit codepoints rather than raw literals in source, so the regex can't
# be corrupted by an editor/terminal normalizing invisible characters.
_INVISIBLE_POINTS = [
    0x200B,  # zero-width space
    0x200C,  # zero-width non-joiner
    0x200D,  # zero-width joiner
    0x200E,  # left-to-right mark
    0x200F,  # right-to-left mark
    0x2060,  # word joiner
    0x2061,  # function application
    0x2062,  # invisible times
    0x2063,  # invisible separator
    0x2064,  # invisible plus
    0xFEFF,  # BOM / zero-width no-break space
    0x00AD,  # soft hyphen
]
_INVISIBLE_RANGES = [
    (0x202A, 0x202E),  # bidi embedding/override
    (0x2066, 0x2069),  # bidi isolate
    (0xE0000, 0xE007F),  # Unicode tag characters (steganography channel)
    (0xFE00, 0xFE0F),  # variation selectors
]

_class_parts = [re.escape(chr(cp)) for cp in _INVISIBLE_POINTS]
_class_parts += [f"{chr(lo)}-{chr(hi)}" for lo, hi in _INVISIBLE_RANGES]
_INVISIBLE = re.compile("[" + "".join(_class_parts) + "]")

# Non-printing control chars except common whitespace (tab, newline, CR)
_CONTROL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize(text: str) -> str:
    if not text:
        return text
    text = _INVISIBLE.sub("", text)
    text = _CONTROL.sub("", text)
    text = unicodedata.normalize("NFC", text)
    return text


def was_modified(original: str, cleaned: str) -> bool:
    return original != cleaned
