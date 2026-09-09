import pytest

from app.services.parsing import DocumentParseError, parse_markdown


def test_markdown_preserves_headings() -> None:
    sections = parse_markdown("# Giriş\nİlk bölüm\n## Sonuç\nİkinci bölüm".encode())

    assert [section.heading for section in sections] == ["Giriş", "Sonuç"]
    assert "İlk bölüm" in sections[0].text


def test_empty_markdown_is_rejected() -> None:
    with pytest.raises(DocumentParseError):
        parse_markdown(b"  \n")

