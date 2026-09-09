import math
import re
from dataclasses import dataclass

from app.services.parsing import ExtractedSection


@dataclass(slots=True)
class TextChunk:
    content: str
    position: int
    token_count: int
    page: int | None
    heading: str | None


def estimate_tokens(text: str) -> int:
    return max(1, math.ceil(len(re.findall(r"\w+|[^\w\s]", text)) * 1.25))


def chunk_sections(
    sections: list[ExtractedSection], max_chars: int = 3200, overlap_chars: int = 480
) -> list[TextChunk]:
    if max_chars <= overlap_chars:
        raise ValueError("max_chars overlap_chars değerinden büyük olmalıdır.")

    chunks: list[TextChunk] = []
    for section in sections:
        text = section.text.strip()
        start = 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            if end < len(text):
                boundary = text.rfind("\n", start + max_chars // 2, end)
                if boundary < 0:
                    boundary = text.rfind(" ", start + max_chars // 2, end)
                if boundary > start:
                    end = boundary

            content = text[start:end].strip()
            if content:
                chunks.append(
                    TextChunk(
                        content=content,
                        position=len(chunks),
                        token_count=estimate_tokens(content),
                        page=section.page,
                        heading=section.heading,
                    )
                )
            if end >= len(text):
                break
            start = max(start + 1, end - overlap_chars)

    if not chunks:
        raise ValueError("Belgeden chunk üretilemedi.")
    return chunks

