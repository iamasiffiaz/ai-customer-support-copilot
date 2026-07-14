import os
import re
import uuid
from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".md"}


def ensure_upload_dir(upload_dir: str) -> Path:
    path = Path(upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(filename: str) -> str:
    name = Path(filename).name
    stem = re.sub(r"[^a-zA-Z0-9._-]", "_", Path(name).stem)[:80]
    ext = Path(name).suffix.lower()
    return f"{stem}_{uuid.uuid4().hex[:8]}{ext}"


def is_allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def get_file_type(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")
