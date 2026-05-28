"""Eval dataset loading and validation."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class EvalDocument:
    id: str
    name: str
    content: str


@dataclass(frozen=True)
class EvalQuestion:
    question: str
    expected_doc_id: str
    expected_chunk_substrings: List[str]
    expected_answer_substrings: List[str]


@dataclass(frozen=True)
class EvalDataset:
    name: str
    documents: List[EvalDocument]
    questions: List[EvalQuestion]


def load_dataset(path: str | Path) -> EvalDataset:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    documents = [
        EvalDocument(id=d["id"], name=d["name"], content=d["content"])
        for d in raw.get("documents", [])
    ]
    questions = [
        EvalQuestion(
            question=q["question"],
            expected_doc_id=q["expected_doc_id"],
            expected_chunk_substrings=list(q.get("expected_chunk_substrings", [])),
            expected_answer_substrings=list(q.get("expected_answer_substrings", [])),
        )
        for q in raw.get("questions", [])
    ]
    _validate(documents, questions)
    return EvalDataset(name=raw.get("name", Path(path).stem), documents=documents, questions=questions)


def _validate(documents: List[EvalDocument], questions: List[EvalQuestion]) -> None:
    doc_ids = {d.id for d in documents}
    if not doc_ids:
        raise ValueError("dataset must include at least one document")
    if not questions:
        raise ValueError("dataset must include at least one question")
    for q in questions:
        if q.expected_doc_id not in doc_ids:
            raise ValueError(
                f"question references unknown document_id: {q.expected_doc_id!r}"
            )
