"""Tests for the RAG orchestrator using fake providers."""
from __future__ import annotations

import pytest

from services.rag import RagService
from services.vector_store import Chunk, RetrievalResult

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeEmbeddings:
    def __init__(self):
        self.embed_calls = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.embed_calls.append(list(texts))
        # Deterministic dummy vectors: each text -> a 4-d vector based on length
        return [[float(len(t)), 0.0, 0.0, 0.0] for t in texts]


class FakeGenerator:
    def __init__(self, response: str = "The answer is X [1]."):
        self.response = response
        self.last_prompt = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


class FakeStore:
    def __init__(self, retrieval_results: list[RetrievalResult] | None = None):
        self.added: list[tuple] = []
        self._results = retrieval_results or []

    def add_chunks(self, chunks, embeddings):
        self.added.append((list(chunks), list(embeddings)))

    def query(self, embedding, top_k=5):
        return self._results[:top_k]


def _result(idx: int, doc_name: str, text: str, score: float = 0.9) -> RetrievalResult:
    return RetrievalResult(
        chunk=Chunk(
            id=f"d::{idx}", text=text, document_id="d",
            document_name=doc_name, chunk_index=idx,
        ),
        score=score,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_index_document_chunks_and_stores():
    embeddings = FakeEmbeddings()
    store = FakeStore()
    rag = RagService(embeddings=embeddings, generation=FakeGenerator(), store=store)

    text = "This is paragraph one.\n\n" + "Sentence. " * 200
    n = rag.index_document("doc-1", "doc.txt", text)

    assert n > 0
    assert len(store.added) == 1
    chunks, embs = store.added[0]
    assert len(chunks) == n
    assert len(embs) == n
    # All chunks tagged with the right document metadata
    for c in chunks:
        assert c.document_id == "doc-1"
        assert c.document_name == "doc.txt"


def test_index_empty_text_indexes_nothing():
    store = FakeStore()
    rag = RagService(embeddings=FakeEmbeddings(), generation=FakeGenerator(), store=store)
    assert rag.index_document("d", "empty.txt", "") == 0
    assert store.added == []


def test_answer_returns_helpful_message_when_corpus_empty():
    rag = RagService(
        embeddings=FakeEmbeddings(),
        generation=FakeGenerator(),
        store=FakeStore(retrieval_results=[]),
    )
    result = rag.answer("Anything?")
    assert result.retrieved == 0
    assert "upload a document" in result.answer.lower()
    assert result.citations == []


def test_answer_builds_prompt_with_numbered_context():
    gen = FakeGenerator(response="The capital is Paris [1].")
    store = FakeStore(retrieval_results=[
        _result(0, "geo.txt", "France's capital is Paris."),
        _result(1, "geo.txt", "Berlin is the capital of Germany."),
    ])
    rag = RagService(embeddings=FakeEmbeddings(), generation=gen, store=store)

    result = rag.answer("What is the capital of France?")

    assert "Paris" in result.answer
    assert "[1]" in gen.last_prompt
    assert "[2]" in gen.last_prompt
    assert "France's capital is Paris." in gen.last_prompt
    assert result.retrieved == 2


def test_answer_filters_citations_to_those_referenced():
    gen = FakeGenerator(response="Only the second source matters [2].")
    store = FakeStore(retrieval_results=[
        _result(0, "a.txt", "Alpha."),
        _result(1, "b.txt", "Beta."),
        _result(2, "c.txt", "Gamma."),
    ])
    rag = RagService(embeddings=FakeEmbeddings(), generation=gen, store=store)
    result = rag.answer("which one?")
    cited_names = [c.document_name for c in result.citations]
    assert cited_names == ["b.txt"]


def test_answer_returns_all_citations_when_none_referenced():
    gen = FakeGenerator(response="No square brackets here.")
    store = FakeStore(retrieval_results=[
        _result(0, "a.txt", "Alpha."),
        _result(1, "b.txt", "Beta."),
    ])
    rag = RagService(embeddings=FakeEmbeddings(), generation=gen, store=store)
    result = rag.answer("?")
    assert len(result.citations) == 2


def test_answer_rejects_empty_question():
    rag = RagService(embeddings=FakeEmbeddings(), generation=FakeGenerator(), store=FakeStore())
    with pytest.raises(ValueError):
        rag.answer("   ")
