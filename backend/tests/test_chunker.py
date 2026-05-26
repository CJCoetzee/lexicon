"""Tests for the recursive chunker."""
from __future__ import annotations

from services.chunker import ChunkConfig, chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []


def test_short_text_returns_single_chunk():
    text = "Just a short sentence."
    assert chunk_text(text) == [text]


def test_long_text_splits_into_multiple_chunks():
    paragraph = "This is a sentence. " * 200  # ~4000 chars
    chunks = chunk_text(paragraph, ChunkConfig(chunk_size=400, chunk_overlap=0))
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 400 + 1  # +1 for trailing punctuation tolerance


def test_chunks_have_overlap_when_configured():
    text = "para1\n\n" + ("Sentence. " * 80) + "\n\npara2 " + ("More words. " * 60)
    chunks = chunk_text(text, ChunkConfig(chunk_size=300, chunk_overlap=50))
    assert len(chunks) >= 2
    # The second chunk should start with the trailing characters of the first.
    overlap = chunks[0][-50:]
    assert chunks[1].startswith(overlap)


def test_prefers_paragraph_boundaries():
    text = "First paragraph content here.\n\nSecond paragraph content here."
    chunks = chunk_text(text, ChunkConfig(chunk_size=40, chunk_overlap=0))
    # Each paragraph should appear in its own chunk (or split further), not
    # mid-word with the other paragraph.
    assert any("First paragraph" in c for c in chunks)
    assert any("Second paragraph" in c for c in chunks)


def test_chunks_are_stripped():
    text = "  hello world  "
    assert chunk_text(text) == ["hello world"]
