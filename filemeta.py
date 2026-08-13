"""Strip identifying metadata from files: EXIF/IPTC/XMP in images, the
Info dict and XMP in PDFs, and author/company properties plus reviewer
identity (tracked changes, comments) in Office files.
Never mutates the original -- always writes a "<name>.clean<ext>" copy."""
import re
import shutil
import zipfile
from pathlib import Path

from PIL import Image, ImageSequence

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp", ".bmp"}
OFFICE_EXTS = {".docx", ".xlsx", ".pptx"}

_OFFICE_METADATA_ENTRIES = {"docProps/core.xml", "docProps/app.xml", "docProps/custom.xml"}

_MINIMAL_CORE_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/"></cp:coreProperties>'
)

# docProps only covers document-level properties. Reviewer names also live
# inside the content parts themselves: Word tracked changes and comments,
# Word 365's people list, Excel's (legacy + threaded) comment authors, and
# PowerPoint's comment authors. Each of these is a small, fixed set of start
# tags, so we find those tags first and only touch identity attributes
# *inside* a matched tag -- never a bare attribute-name search over the whole
# file -- so ordinary document text (which could coincidentally contain a
# substring like `author="x"`) is never at risk of being rewritten.
_IDENTITY_TAGS = re.compile(
    rb"<(?:w:(?:ins|del|moveFrom|moveTo|rPrChange|pPrChange|tblPrChange|trPrChange|tcPrChange)"
    rb"|w:comment|w15:person|w15:presenceInfo|p:cmAuthor|person)\b[^>]*>"
)
_IDENTITY_ATTRS = re.compile(rb'((?:\w+:)?(?:author|initials|name|displayName|userId))="[^"]*"')
_IDENTITY_ELEMENTS = re.compile(rb"(<(?:\w+:)?[Aa]uthor(?:\s[^>]*)?>)[^<]*(</(?:\w+:)?[Aa]uthor>)")


def _scrub_reviewer_identity(data: bytes) -> bytes:
    data = _IDENTITY_TAGS.sub(lambda m: _IDENTITY_ATTRS.sub(rb'\1=""', m.group(0)), data)
    data = _IDENTITY_ELEMENTS.sub(rb"\1\2", data)
    return data


def output_path_for(path: Path) -> Path:
    return path.with_name(f"{path.stem}.clean{path.suffix}")


def clean_image(path: Path, out_path: Path):
    # Re-save without ever passing along exif/icc/text metadata, rather than
    # decoding to raw pixels and rebuilding a new image: that round trip
    # forces a lossy JPEG re-encode at PIL's default quality, and it drops
    # the source palette for "P"-mode images (new blank image = new default
    # palette, so old color indices point at the wrong colors). Pillow's
    # save() only writes metadata that's explicitly passed as a kwarg, so a
    # plain save() already omits it.
    img = Image.open(path)
    save_kwargs = {"quality": "keep"} if img.format == "JPEG" else {}
    if getattr(img, "n_frames", 1) > 1:
        frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
        frames[0].save(out_path, save_all=True, append_images=frames[1:], **save_kwargs)
    else:
        img.save(out_path, **save_kwargs)


def clean_pdf(path: Path, out_path: Path):
    import pikepdf

    with pikepdf.open(path) as pdf:
        with pdf.open_metadata() as meta:
            meta.clear()
        if "/Info" in pdf.trailer:
            del pdf.trailer["/Info"]
        pdf.save(out_path)


def clean_office(path: Path, out_path: Path):
    with zipfile.ZipFile(path, "r") as src, zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            if item.filename == "docProps/core.xml":
                dst.writestr(item, _MINIMAL_CORE_XML)
            elif item.filename in _OFFICE_METADATA_ENTRIES:
                continue
            elif item.filename.endswith((".xml", ".vml")):
                dst.writestr(item, _scrub_reviewer_identity(src.read(item.filename)))
            else:
                dst.writestr(item, src.read(item.filename))


def clean_file(path: str) -> Path:
    src = Path(path)
    out = output_path_for(src)
    ext = src.suffix.lower()
    if ext in IMAGE_EXTS:
        clean_image(src, out)
    elif ext == ".pdf":
        clean_pdf(src, out)
    elif ext in OFFICE_EXTS:
        clean_office(src, out)
    else:
        shutil.copy2(src, out)
    return out
