"""Strip identifying metadata from files: EXIF/IPTC/XMP in images, the
Info dict and XMP in PDFs, and author/company properties in Office files.
Never mutates the original — always writes a "<name>.clean<ext>" copy."""
import shutil
import zipfile
from pathlib import Path

from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".webp", ".bmp"}
OFFICE_EXTS = {".docx", ".xlsx", ".pptx"}

_OFFICE_METADATA_ENTRIES = {"docProps/core.xml", "docProps/app.xml", "docProps/custom.xml"}

_MINIMAL_CORE_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/"></cp:coreProperties>'
)


def output_path_for(path: Path) -> Path:
    return path.with_name(f"{path.stem}.clean{path.suffix}")


def clean_image(path: Path, out_path: Path):
    img = Image.open(path)
    data = list(img.getdata())
    clean = Image.new(img.mode, img.size)
    clean.putdata(data)
    clean.save(out_path)


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
