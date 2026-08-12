import zipfile

import pikepdf
from PIL import Image

from filemeta import clean_file


def test_strips_image_exif(tmp_path):
    src = tmp_path / "photo.jpg"
    img = Image.new("RGB", (10, 10), "red")
    exif = img.getexif()
    exif[271] = "FakeCamera"
    img.save(src, exif=exif)

    out = clean_file(str(src))

    assert out.name == "photo.clean.jpg"
    assert dict(Image.open(out).getexif()) == {}
    assert dict(Image.open(src).getexif()) == {271: "FakeCamera"}  # original untouched


def test_strips_pdf_metadata(tmp_path):
    src = tmp_path / "doc.pdf"
    pdf = pikepdf.new()
    pdf.add_blank_page(page_size=(200, 200))
    pdf.docinfo["/Author"] = "Suspicious Author"
    with pdf.open_metadata() as meta:
        meta["dc:creator"] = ["Suspicious Author"]
    pdf.save(src)

    out = clean_file(str(src))

    with pikepdf.open(out) as cleaned:
        assert "/Info" not in cleaned.trailer
        with cleaned.open_metadata() as meta:
            assert "dc:creator" not in dict(meta)


def test_strips_office_properties(tmp_path):
    src = tmp_path / "report.docx"
    with zipfile.ZipFile(src, "w") as z:
        z.writestr("docProps/core.xml", "<coreProperties><dc:creator>Someone</dc:creator></coreProperties>")
        z.writestr("docProps/app.xml", "<Properties><Company>SecretCorp</Company></Properties>")
        z.writestr("word/document.xml", "<document>hello</document>")

    out = clean_file(str(src))

    with zipfile.ZipFile(out) as z:
        names = z.namelist()
        assert "docProps/app.xml" not in names
        assert b"Someone" not in z.read("docProps/core.xml")
        assert z.read("word/document.xml") == b"<document>hello</document>"
