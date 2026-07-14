"""Text chunking for knowledge base documents."""

from __future__ import annotations

from config import get_settings


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    settings = get_settings()
    chunk_size = chunk_size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap

    text = (text or "").strip()
    if not text:
        return []

    # Prefer section breaks for policy docs
    sections = [s.strip() for s in text.split("\n\n") if s.strip()]
    if len(sections) > 1 and all(len(s) < chunk_size * 1.5 for s in sections):
        chunks: list[str] = []
        buffer = ""
        for section in sections:
            candidate = f"{buffer}\n\n{section}".strip() if buffer else section
            if len(candidate) <= chunk_size:
                buffer = candidate
            else:
                if buffer:
                    chunks.append(buffer)
                if len(section) <= chunk_size:
                    buffer = section
                else:
                    chunks.extend(_window(section, chunk_size, overlap))
                    buffer = ""
        if buffer:
            chunks.append(buffer)
        return chunks

    return _window(text, chunk_size, overlap)


def _window(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        if end < length:
            window = text[start:end]
            break_at = max(window.rfind("\n\n"), window.rfind(". "), window.rfind("\n"))
            if break_at > chunk_size * 0.4:
                end = start + break_at + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= length:
            break
        start = max(0, end - overlap)
    return chunks
