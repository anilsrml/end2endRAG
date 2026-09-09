import pytest

from app.services.chunking import chunk_sections
from app.services.parsing import ExtractedSection


def test_short_section_becomes_one_chunk() -> None:
    chunks = chunk_sections([ExtractedSection("Kısa bir metin.", heading="Başlık")])

    assert len(chunks) == 1
    assert chunks[0].heading == "Başlık"
    assert chunks[0].position == 0
    assert chunks[0].token_count > 0


def test_long_section_is_split_with_overlap() -> None:
    text = " ".join(f"kelime-{index}" for index in range(300))
    chunks = chunk_sections([ExtractedSection(text)], max_chars=300, overlap_chars=50)

    assert len(chunks) > 1
    assert [chunk.position for chunk in chunks] == list(range(len(chunks)))


def test_invalid_chunk_configuration_is_rejected() -> None:
    with pytest.raises(ValueError):
        chunk_sections([ExtractedSection("metin")], max_chars=100, overlap_chars=100)

