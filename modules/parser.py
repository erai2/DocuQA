"""Utilities for reading and preprocessing uploaded documents."""
from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Final, Iterable, List

_TEXT_ENCODING_CANDIDATES: Final[Iterable[str]] = (
    "utf-8",
    "utf-16",
    "cp949",
    "euc-kr",
)


def _decode_bytes(raw: bytes) -> str:
    for encoding in _TEXT_ENCODING_CANDIDATES:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    # Fallback to latin-1 which never fails, while preserving bytes information.
    return raw.decode("latin-1")


def extract_text(uploaded_file) -> str:
    """Extract text from a Streamlit UploadedFile instance.

    Parameters
    ----------
    uploaded_file:
        Streamlit UploadedFile-like object.

    Returns
    -------
    str
        Extracted text content.
    """

    filename = getattr(uploaded_file, "name", "") or "uploaded"
    suffix = Path(filename).suffix.lower()
    raw_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    if suffix == ".txt":
        return _decode_bytes(raw_bytes)

    if suffix == ".pdf":
        try:
            import PyPDF2  # type: ignore
        except ImportError as exc:
            raise RuntimeError("PyPDF2 라이브러리가 필요합니다. requirements.txt를 확인하세요.") from exc

        reader = PyPDF2.PdfReader(io.BytesIO(raw_bytes))
        extracted = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(extracted)

    if suffix == ".docx":
        try:
            import docx  # type: ignore
        except ImportError as exc:
            raise RuntimeError("python-docx 라이브러리가 필요합니다. requirements.txt를 확인하세요.") from exc

        document = docx.Document(io.BytesIO(raw_bytes))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    raise ValueError(f"지원하지 않는 파일 형식입니다: {suffix}")


_SENTENCE_BOUNDARY_PATTERN: Final[re.Pattern[str]] = re.compile(r"(?<=[.!?\n])\s+")


def split_sentences(text: str) -> List[str]:
    """Split raw text into sentences with lightweight heuristics."""

    stripped = text.strip()
    if not stripped:
        return []

    candidates = re.split(_SENTENCE_BOUNDARY_PATTERN, stripped)
    sentences: List[str] = []
    for candidate in candidates:
        cleaned = candidate.strip()
        if cleaned:
            sentences.append(cleaned)
    return sentences
