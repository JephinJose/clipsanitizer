from sanitize import sanitize


def test_strips_zero_width():
    assert sanitize("hel​lo") == "hello"


def test_strips_bidi_override():
    assert sanitize("a‮b‬c") == "abc"


def test_strips_unicode_tags():
    assert sanitize("id\U000e0031\U000e0032text") == "idtext"


def test_keeps_normal_text():
    s = "Hello, world!\nSecond line.\tTabbed."
    assert sanitize(s) == s


def test_empty():
    assert sanitize("") == ""
