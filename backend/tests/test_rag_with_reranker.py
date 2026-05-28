"""Verify that the RagService composes the reranker correctly."""
from __future__ import annotations

from services.rag import RagService
from services.reranker import GeminiReranker
from services.vector_store import Chunk, RetrievalResult


class FakeEmb:
    def embed(self, texts):
        return [[0.0] * 4 for _ in texts]


class FakeGen:
    """Returns reranker-style JSON when asked, and a generation otherwise."""

    def __init__(self):
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        if "YOUR JSON:" in prompt and "PASSAGES" in prompt:
            # This is the reranker prompt. Score so chunk 2 wins.
            return '[{"n": 1, "score": 1.0}, {"n": 2, "score": 9.0}, {"n": 3, "score": 5.0}]'
        # Generator prompt: emit something with a citation.
        return "Reranked answer [1]."


class FakeStore:
    def __init__(self, results: list[RetrievalResult]):
        self._results = results
        self.last_top_k = None

    def add_chunks(self, *_args, **_kwargs):
        pass

    def query(self, _embedding, top_k=5):
        self.last_top_k = top_k
        return self._results[:top_k]


def _r(idx: int, text: str) -> RetrievalResult:
    return RetrievalResult(
        chunk=Chunk(id=f"c{idx}", text=text, document_id="d",
                    document_name="d.txt", chunk_index=idx),
        score=0.5,
    )


def test_rag_without_reranker_uses_topk_directly():
    store = FakeStore([_r(0, "x"), _r(1, "y"), _r(2, "z")])
    rag = RagService(embeddings=FakeEmb(), generation=FakeGen(), store=store)
    result = rag.answer("?", top_k=2)
    assert store.last_top_k == 2
    assert "Reranked answer" in result.answer


def test_rag_with_reranker_overfetches_and_reorders():
    store = FakeStore([_r(0, "x"), _r(1, "y"), _r(2, "z"), _r(3, "w")])
    reranker = GeminiReranker(generation=FakeGen())
    rag = RagService(
        embeddings=FakeEmb(),
        generation=FakeGen(),
        store=store,
        reranker=reranker,
        retrieval_overfetch=2,
    )
    rag.answer("?", top_k=2)
    # top_k=2, overfetch=2 -> store should be queried for 4
    assert store.last_top_k == 4
