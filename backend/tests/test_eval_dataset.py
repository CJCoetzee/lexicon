"""Tests for eval dataset loading and validation."""
from __future__ import annotations

import json

import pytest

from eval.dataset import load_dataset


def _write_dataset(tmp_path, payload):
    path = tmp_path / "data.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_loads_valid_dataset(tmp_path):
    path = _write_dataset(tmp_path, {
        "name": "tiny",
        "documents": [{"id": "d1", "name": "d1.txt", "content": "alpha"}],
        "questions": [{
            "question": "What?", "expected_doc_id": "d1",
            "expected_chunk_substrings": ["alpha"],
            "expected_answer_substrings": ["alpha"],
        }],
    })
    ds = load_dataset(path)
    assert ds.name == "tiny"
    assert len(ds.documents) == 1
    assert ds.documents[0].id == "d1"
    assert len(ds.questions) == 1
    assert ds.questions[0].expected_doc_id == "d1"


def test_rejects_empty_documents(tmp_path):
    path = _write_dataset(tmp_path, {
        "documents": [],
        "questions": [{"question": "?", "expected_doc_id": "x",
                       "expected_chunk_substrings": [], "expected_answer_substrings": []}],
    })
    with pytest.raises(ValueError, match="at least one document"):
        load_dataset(path)


def test_rejects_empty_questions(tmp_path):
    path = _write_dataset(tmp_path, {
        "documents": [{"id": "d", "name": "d.txt", "content": "x"}],
        "questions": [],
    })
    with pytest.raises(ValueError, match="at least one question"):
        load_dataset(path)


def test_rejects_unknown_doc_id_reference(tmp_path):
    path = _write_dataset(tmp_path, {
        "documents": [{"id": "d1", "name": "d1.txt", "content": "x"}],
        "questions": [{"question": "?", "expected_doc_id": "d2",
                       "expected_chunk_substrings": [], "expected_answer_substrings": []}],
    })
    with pytest.raises(ValueError, match="unknown document_id"):
        load_dataset(path)
