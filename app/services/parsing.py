import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path


class DocumentParseError(ValueError):
    pass


@dataclass(slots=True)
class ExtractedSection:
    text: str
    page: int | None = None
    heading: str | None = None


def parse_document(filename: str, data: bytes) -> tuple[str, list[ExtractedSection]]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".md":
        return "text/markdown", parse_markdown(data)
    if suffix == ".pdf":
        return "application/pdf", parse_pdf(data)
    raise DocumentParseError("Yalnızca .md ve .pdf dosyaları destekleniyor.")


def parse_markdown(data: bytes) -> list[ExtractedSection]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentParseError("Markdown dosyası UTF-8 olmalıdır.") from exc

    sections: list[ExtractedSection] = []
    current_heading: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        content = "\n".join(buffer).strip()
        if content:
            sections.append(ExtractedSection(text=content, heading=current_heading))
        buffer.clear()

    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            flush()
            current_heading = match.group(1).strip()
            buffer.append(line)
        else:
            buffer.append(line)
    flush()

    if not sections:
        raise DocumentParseError("Belgede indekslenecek metin bulunamadı.")
    return sections


def parse_pdf(data: bytes) -> list[ExtractedSection]:
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(data))
    except Exception as exc:
        raise DocumentParseError("PDF okunamadı veya bozuk.") from exc

    sections = [
        ExtractedSection(text=text, page=number)
        for number, page in enumerate(reader.pages, start=1)
        if (text := (page.extract_text() or "").strip())
    ]
    if not sections:
        raise DocumentParseError("PDF metin katmanı içermiyor; OCR henüz desteklenmiyor.")
    return sections

