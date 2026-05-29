"""Pytest fixtures."""
from __future__ import annotations

from dataclasses import dataclass

import pytest

from app import create_app
from services.rag import AnswerResult, Citation

# ---------------------------------------------------------------------------
# Fakes -- keep tests fast and offline (no Gemini, no Chroma on disk).
# ---------------------------------------------------------------------------


@dataclass
class FakeRagService:
    """Records calls and returns canned responses."""

    indexed_documents: list[tuple] = None  # type: ignore[assignment]
    next_answer: AnswerResult = None        # type: ignore[assignment]

    def __post_init__(self):
        if self.indexed_documents is None:
            self.indexed_documents = []
        if self.next_answer is None:
            self.next_answer = AnswerResult(
                answer="A canned answer with a citation [1].",
                citations=[
                    Citation(
                        n=1,
                        document_name="example.txt",
                        document_id="doc-1",
                        chunk_index=0,
                        text="Lorem ipsum.",
                        score=0.9,
                    )
                ],
                latency_ms=42,
                retrieved=1,
            )

    def index_document(self, document_id: str, document_name: str, text: str) -> int:
        self.indexed_documents.append((document_id, document_name, text))
        return max(1, len(text) // 600)

    def answer(self, question: str, top_k: int = 5, history=None):
        return self.next_answer

    def answer_stream(self, question: str, top_k: int = 5, history=None):
        """Yield the canned answer as a single token + a done event."""
        yield {"type": "token", "text": self.next_answer.answer}
        yield {
            "type": "done",
            "citations": [
                {
                    "n": c.n,
                    "document_name": c.document_name,
                    "document_id": c.document_id,
                    "chunk_index": c.chunk_index,
                    "text": c.text,
                    "score": c.score,
                }
                for c in self.next_answer.citations
            ],
            "latency_ms": self.next_answer.latency_ms,
            "retrieved": self.next_answer.retrieved,
        }


@pytest.fixture()
def fake_rag(monkeypatch):
    fake = FakeRagService()
    monkeypatch.setattr("routes.documents.get_rag_service", lambda: fake)
    monkeypatch.setattr("routes.chat.get_rag_service", lambda: fake)
    return fake


@pytest.fixture()
def app(fake_rag):
    application = create_app()
    application.config.update({"TESTING": True})
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()
