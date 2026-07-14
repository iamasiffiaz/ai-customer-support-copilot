"""Extract text from uploaded support documents."""

from __future__ import annotations

from pathlib import Path


def extract_text_from_file(path: str, file_type: str) -> str:
    file_type = (file_type or Path(path).suffix.lstrip(".")).lower()
    if file_type in ("txt", "md"):
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    if file_type == "pdf":
        return _extract_pdf(path)
    if file_type == "docx":
        return _extract_docx(path)
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def _extract_pdf(path: str) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text)
        return "\n\n".join(pages).strip()
    except Exception as exc:
        return f"[PDF extraction failed: {exc}]"


def _extract_docx(path: str) -> str:
    try:
        from docx import Document

        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip()).strip()
    except Exception as exc:
        return f"[DOCX extraction failed: {exc}]"
