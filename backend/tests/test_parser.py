"""Tests for the document parser strategy."""
from __future__ import annotations

import io

import pytest

from services.parser import (
    UnsupportedFileTypeError,
    parse_document,
    supported_extensions,
)


def test_supported_extensions_includes_expected_types():
    extensions = set(supported_extensions())
    assert {".pdf", ".txt", ".md"}.issubset(extensions)


def test_parses_plain_text_utf8():
    stream = io.BytesIO("Hello, Lexicon!".encode("utf-8"))
    text = parse_document("notes.txt", stream)
    assert text == "Hello, Lexicon!"


def test_parses_markdown_as_text():
    stream = io.BytesIO(b"# Heading\n\nSome content.")
    text = parse_document("readme.md", stream)
    assert "Heading" in text
    assert "Some content." in text


def test_falls_back_to_latin1_when_utf8_decode_fails():
    # A byte sequence that's invalid UTF-8 but valid latin-1.
    stream = io.BytesIO(b"caf\xe9")
    text = parse_document("note.txt", stream)
    assert "caf" in text


def test_unsupported_extension_raises():
    stream = io.BytesIO(b"<html></html>")
    with pytest.raises(UnsupportedFileTypeError):
        parse_document("page.html", stream)


def test_unknown_extension_raises_with_helpful_message():
    stream = io.BytesIO(b"data")
    with pytest.raises(UnsupportedFileTypeError, match="not supported"):
        parse_document("data.bin", stream)
