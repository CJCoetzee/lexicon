"""Tests for the Gemini reranker."""
from __future__ import annotations

from services.reranker import GeminiReranker, _parse_scores
from services.vector_store import Chunk, RetrievalResult


class FakeGen:
    def __init__(self, output: str):
        self.output = output
        self.last_prompt = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.output


def _r(idx: int, text: str, score: float = 0.5) -> RetrievalResult:
    return RetrievalResult(
        chunk=Chunk(id=f"c{idx}", text=text, document_id="d",
                    document_name="d.txt", chunk_index=idx),
        score=score,
    )


def test_reranks_by_score_descending():
    gen = FakeGen('[{"n": 1, "score": 2.0}, {"n": 2, "score": 9.0}, {"n": 3, "score": 5.0}]')
    rr = GeminiReranker(generation=gen)
    out = rr.rerank("q", [_r(0, "a"), _r(1, "b"), _r(2, "c")])
    assert [s.result.chunk.id for s in out] == ["c1", "c2", "c0"]
    assert [s.rerank_score for s in out] == [9.0, 5.0, 2.0]


def test_handles_empty_input():
    rr = GeminiReranker(generation=FakeGen("[]"))
    assert rr.rerank("q", []) == []


def test_missing_scores_default_to_zero_and_sink():
    gen = FakeGen('[{"n": 2, "score": 7}]')  # only scores chunk 2
    rr = GeminiReranker(generation=gen)
    out = rr.rerank("q", [_r(0, "a"), _r(1, "b"), _r(2, "c")])
    assert out[0].result.chunk.id == "c1"  # the scored one
    assert out[0].rerank_score == 7.0
    assert out[1].rerank_score == 0.0
    assert out[2].rerank_score == 0.0


def test_clamps_score_to_zero_ten():
    assert _parse_scores('[{"n": 1, "score": 99}]', expected_n=1) == {1: 10.0}
    assert _parse_scores('[{"n": 1, "score": -5}]', expected_n=1) == {1: 0.0}


def test_ignores_out_of_range_indices():
    scores = _parse_scores('[{"n": 5, "score": 9}]', expected_n=2)
    assert scores == {}


def test_returns_empty_on_unparseable_output():
    assert _parse_scores("not json", expected_n=3) == {}
    assert _parse_scores("{not an array}", expected_n=3) == {}
