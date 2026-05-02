"""Document text extraction.

Designed as a small Strategy pattern: each supported file type maps to an
extractor function. Adding a new format is a one-line registry change, which
we'll lean on in Sprint 2 if we add .docx or .html support.
"""
from __future__ import annotations

import io
import os
from typing import Callable, Dict, IO, Iterable

from pypdf import PdfReader


class UnsupportedFileTypeError(ValueError):
    """Raised when an uploaded file's extension is not in the registry."""


def _extract_pdf(stream: IO[bytes]) -> str:
    reader = PdfReader(stream)
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:  # noqa: BLE001 — bad pages shouldn't kill the upload
            pages.append("")
    return "\n\n".join(pages).strip()


def _extract_text(stream: IO[bytes]) -> str:
    raw = stream.read()
    if isinstance(raw, bytes):
        # Try UTF-8 first; fall back to latin-1 which never raises.
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin-1")
    return str(raw)


# Registry of extension -> extractor.
# Strategy pattern: callers don't need to know about each format.
_EXTRACTORS: Dict[str, Callable[[IO[bytes]], str]] = {
    ".pdf": _extract_pdf,
    ".txt": _extract_text,
    ".md": _extract_text,
}


def supported_extensions() -> Iterable[str]:
    return _EXTRACTORS.keys()


def parse_document(filename: str, stream: IO[bytes]) -> str:
    """Return the extracted plain text of a document.

    Args:
        filename: original filename — used to determine file type by extension.
        stream:   a binary file-like stream positioned at the start.

    Raises:
        UnsupportedFileTypeError: if no extractor is registered for the type.
    """
    _, ext = os.path.splitext(filename.lower())
    extractor = _EXTRACTORS.get(ext)
    if extractor is None:
        raise UnsupportedFileTypeError(
            f"File type '{ext or '(none)'}' is not supported."
        )

    # Some extractors (pypdf) want a real seekable stream.
    if not hasattr(stream, "seek"):
        stream = io.BytesIO(stream.read())

    return extractor(stream)
