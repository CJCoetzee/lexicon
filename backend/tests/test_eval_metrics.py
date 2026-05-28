"""Tests for eval metrics."""
from __future__ import annotations

from eval.metrics import (
    PerQuestionRecord,
    answer_match_rate,
    estimated_cost,
    gold_rank,
    latency_percentiles,
    mean_faithfulness,
    mean_reciprocal_rank,
    recall_at_k,
)


def _record(
    *,
    expected_doc_id="d1",
    retrieved_doc_ids=None,
    retrieved_chunk_texts=None,
    expected_chunk_substrings=None,
    answer="",
    expected_answer_substrings=None,
    latency_ms=100,
    faithfulness=None,
):
    return PerQuestionRecord(
        question="?", expected_doc_id=expected_doc_id,
        retrieved_doc_ids=retrieved_doc_ids or [],
        retrieved_chunk_texts=retrieved_chunk_texts or [],
        expected_chunk_substrings=expected_chunk_substrings or [],
        answer=answer,
        expected_answer_substrings=expected_answer_substrings or [],
        latency_ms=latency_ms,
        input_chars=100, output_chars=50,
        faithfulness_score=faithfulness,
    )


def test_gold_rank_finds_chunk_with_all_substrings():
    rec = _record(
        retrieved_doc_ids=["d2", "d1", "d1"],
        retrieved_chunk_texts=["irrelevant", "noise", "alpha and beta here"],
        expected_chunk_substrings=["alpha", "beta"],
    )
    assert gold_rank(rec) == 3


def test_gold_rank_falls_back_to_doc_match_when_substrings_missing():
    rec = _record(
        retrieved_doc_ids=["d2", "d1"],
        retrieved_chunk_texts=["x", "y"],
        expected_chunk_substrings=["never"],
    )
    assert gold_rank(rec) == 2


def test_gold_rank_returns_none_when_doc_not_retrieved():
    rec = _record(retrieved_doc_ids=["d2", "d3"], retrieved_chunk_texts=["x", "y"])
    assert gold_rank(rec) is None


def test_recall_at_k_counts_hits_within_k():
    records = [
        _record(retrieved_doc_ids=["d1"], retrieved_chunk_texts=["alpha"], expected_chunk_substrings=["alpha"]),
        _record(retrieved_doc_ids=["d2"], retrieved_chunk_texts=["x"]),
    ]
    assert recall_at_k(records, 1) == 0.5
    assert recall_at_k(records, 5) == 0.5


def test_mrr_is_average_reciprocal():
    records = [
        _record(retrieved_doc_ids=["d1"], retrieved_chunk_texts=["alpha"], expected_chunk_substrings=["alpha"]),
        _record(retrieved_doc_ids=["d2", "d1"], retrieved_chunk_texts=["x", "alpha"], expected_chunk_substrings=["alpha"]),
    ]
    # 1/1 + 1/2 = 1.5; / 2 = 0.75
    assert mean_reciprocal_rank(records) == 0.75


def test_answer_match_rate_uses_expected_substrings():
    records = [
        _record(answer="The capital is Paris.", expected_answer_substrings=["Paris"]),
        _record(answer="Berlin is in Germany.", expected_answer_substrings=["Paris"]),
        _record(answer="No expected", expected_answer_substrings=[]),  # excluded
    ]
    assert answer_match_rate(records) == 0.5


def test_mean_faithfulness_ignores_none():
    records = [
        _record(faithfulness=0.8),
        _record(faithfulness=0.6),
        _record(faithfulness=None),
    ]
    assert mean_faithfulness(records) == 0.7


def test_mean_faithfulness_returns_none_when_no_scores():
    assert mean_faithfulness([_record()]) is None


def test_latency_percentiles_handles_small_n():
    records = [_record(latency_ms=100), _record(latency_ms=200), _record(latency_ms=300)]
    pct = latency_percentiles(records)
    assert pct["p50_ms"] == 200
    assert pct["mean_ms"] == 200


def test_estimated_cost_returns_breakdown_and_per_query():
    records = [_record(latency_ms=10) for _ in range(4)]
    cost = estimated_cost(records)
    assert "per_query_usd" in cost
    assert "breakdown" in cost
    assert cost["per_query_usd"] >= 0
