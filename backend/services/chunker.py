"""Text chunking.

We use a recursive character splitter: try semantic boundaries first
(paragraphs, then sentences, then words), then fall back to character cuts.
A small overlap between chunks reduces the chance that a relevant span gets
sliced down the middle.

Chunk size and overlap are tunable; Sprint 3's eval harness will use the
same interface to compare configurations.
"""
from __future__ import annotations

from dataclasses import dataclass

# Separator order matters — longer / more semantic separators first.
_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass(frozen=True)
class ChunkConfig:
    chunk_size: int = 600
    chunk_overlap: int = 100


def _split_with_separator(text: str, separator: str) -> list[str]:
    if separator == "":
        return list(text)
    if separator == ". ":
        # Keep the period attached to each sentence.
        parts = [s + "." for s in text.split(". ") if s]
        if parts and not text.endswith("."):
            parts[-1] = parts[-1].rstrip(".")
        return parts
    return [p for p in text.split(separator) if p]


def _merge_pieces(pieces: list[str], separator: str, config: ChunkConfig) -> list[str]:
    """Pack pieces into chunks ≤ chunk_size, joining with the separator."""
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        candidate = piece if not current else f"{current}{separator}{piece}"
        if len(candidate) <= config.chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(piece) > config.chunk_size:
                # Piece itself is too big — recurse with the next separator.
                chunks.extend(_recursive_split(piece, _next_separator(separator), config))
                current = ""
            else:
                current = piece
    if current:
        chunks.append(current)
    return chunks


def _next_separator(separator: str) -> str:
    idx = _SEPARATORS.index(separator)
    return _SEPARATORS[min(idx + 1, len(_SEPARATORS) - 1)]


def _recursive_split(text: str, separator: str, config: ChunkConfig) -> list[str]:
    if len(text) <= config.chunk_size:
        return [text]
    pieces = _split_with_separator(text, separator)
    return _merge_pieces(pieces, separator if separator != "" else "", config)


def _add_overlap(chunks: list[str], overlap: int) -> list[str]:
    if overlap <= 0 or len(chunks) <= 1:
        return chunks
    out = [chunks[0]]
    for prev, curr in zip(chunks, chunks[1:], strict=False):
        carry = prev[-overlap:] if len(prev) >= overlap else prev
        out.append(carry + curr)
    return out


def chunk_text(text: str, config: ChunkConfig | None = None) -> list[str]:
    """Split text into overlapping chunks suitable for embedding.

    Empty / whitespace-only input returns an empty list.
    """
    config = config or ChunkConfig()
    text = text.strip()
    if not text:
        return []
    if len(text) <= config.chunk_size:
        return [text]
    base = _recursive_split(text, _SEPARATORS[0], config)
    base = [c.strip() for c in base if c and c.strip()]
    return _add_overlap(base, config.chunk_overlap)
