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


def test_preserves_jpeg_quality(tmp_path):
    src = tmp_path / "photo.jpg"
    img = Image.new("RGB", (200, 200))
    for x in range(200):
        for y in range(200):
            img.putpixel((x, y), ((x * 7) % 256, (y * 13) % 256, ((x + y) * 3) % 256))
    img.save(src, quality=95)

    out = clean_file(str(src))

    # A metadata strip shouldn't silently recompress at PIL's low default
    # quality (75): that would shrink a hard-to-compress image like this by
    # roughly half. Re-encoding at the source's own quality only changes
    # size by a few percent (JPEG headers, no requantization).
    assert out.stat().st_size > src.stat().st_size * 0.85


def test_preserves_palette_image_colors(tmp_path):
    src = tmp_path / "icon.png"
    img = Image.new("P", (10, 10))
    palette = []
    for i in range(256):
        palette += [i, (i * 2) % 256, (i * 3) % 256]
    img.putpalette(palette)
    for x in range(10):
        for y in range(10):
            img.putpixel((x, y), (x * 10 + y) % 256)
    img.save(src)

    out = clean_file(str(src))

    assert list(Image.open(out).convert("RGB").getdata()) == list(Image.open(src).convert("RGB").getdata())


def test_preserves_multiframe_tiff(tmp_path):
    src = tmp_path / "scan.tiff"
    frame1 = Image.new("RGB", (5, 5), "red")
    frame2 = Image.new("RGB", (5, 5), "blue")
    frame1.save(src, save_all=True, append_images=[frame2])

    out = clean_file(str(src))

    assert Image.open(out).n_frames == 2


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


def test_strips_docx_reviewer_identity(tmp_path):
    src = tmp_path / "report.docx"
    document_xml = (
        b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        b'<w:body>'
        b'<w:p><w:r><w:t>A paragraph that literally says author="Not Real" as text.</w:t></w:r></w:p>'
        b'<w:p><w:ins w:id="1" w:author="John Doe" w:date="2024-01-01T00:00:00Z">'
        b'<w:r><w:t>inserted text</w:t></w:r></w:ins></w:p>'
        b'</w:body></w:document>'
    )
    comments_xml = (
        b'<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        b'<w:comment w:id="0" w:author="Jane Doe" w:initials="JD" w:date="2024-01-01T00:00:00Z">'
        b'<w:p><w:r><w:t>a real review comment</w:t></w:r></w:p></w:comment>'
        b'</w:comments>'
    )
    with zipfile.ZipFile(src, "w") as z:
        z.writestr("docProps/core.xml", "<coreProperties/>")
        z.writestr("word/document.xml", document_xml)
        z.writestr("word/comments.xml", comments_xml)

    out = clean_file(str(src))

    with zipfile.ZipFile(out) as z:
        doc = z.read("word/document.xml")
        comments = z.read("word/comments.xml")
    assert b"John Doe" not in doc
    assert b"Jane Doe" not in comments
    assert b'w:initials="JD"' not in comments
    # Tracked-change content and lookalike body text survive untouched.
    assert b"inserted text" in doc
    assert b'author="Not Real"' in doc
    assert b"a real review comment" in comments


def test_strips_xlsx_comment_author(tmp_path):
    src = tmp_path / "book.xlsx"
    comments_xml = (
        b'<comments xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        b'<authors><author>Bob Builder</author></authors>'
        b'<commentList><comment ref="A1" authorId="0"><text><r><t>Check this number</t></r></text></comment></commentList>'
        b'</comments>'
    )
    with zipfile.ZipFile(src, "w") as z:
        z.writestr("docProps/core.xml", "<coreProperties/>")
        z.writestr("xl/comments1.xml", comments_xml)

    out = clean_file(str(src))

    with zipfile.ZipFile(out) as z:
        comments = z.read("xl/comments1.xml")
    assert b"Bob Builder" not in comments
    assert b"Check this number" in comments


def test_strips_pptx_comment_author(tmp_path):
    src = tmp_path / "deck.pptx"
    cmauthors_xml = (
        b'<p:cmAuthorLst xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        b'<p:cmAuthor id="0" name="Alice Reviewer" initials="AR" lastIdx="1" clrIdx="0"/>'
        b'</p:cmAuthorLst>'
    )
    with zipfile.ZipFile(src, "w") as z:
        z.writestr("docProps/core.xml", "<coreProperties/>")
        z.writestr("ppt/commentAuthors.xml", cmauthors_xml)

    out = clean_file(str(src))

    with zipfile.ZipFile(out) as z:
        cmauthors = z.read("ppt/commentAuthors.xml")
    assert b"Alice Reviewer" not in cmauthors
    assert b'initials="AR"' not in cmauthors
    assert b'id="0"' in cmauthors
