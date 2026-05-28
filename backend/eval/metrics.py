"""Eval metrics: retrieval (recall@k, MRR), generation (faithfulness,
answer-substring match), and operational (latency percentiles, cost).

Each function is pure: it takes the raw per-question records and returns
a summary number/dict. The runner orchestrates the loop.
"""
from __future__ import annotations

import statistics
from collections.abc import Sequence
from dataclasses import dataclass, field

# Gemini Flash pricing as of 2026, per million tokens. Adjust if Google
# shifts pricing — these constants live in one place for that reason.
COST_PER_M_INPUT_TOKENS_USD = 0.075
COST_PER_M_OUTPUT_TOKENS_USD = 0.30
COST_PER_M_EMBED_TOKENS_USD = 0.025

# Rough heuristic — Gemini tokenizes ~4 chars per token for English.
CHARS_PER_TOKEN = 4


@dataclass
class PerQuestionRecord:
    question: str
    expected_doc_id: str

    # Retrieval
    retrieved_doc_ids: list[str] = field(default_factory=list)
    retrieved_chunk_texts: list[str] = field(default_factory=list)
    expected_chunk_substrings: list[str] = field(default_factory=list)

    # Generation
    answer: str = ""
    expected_answer_substrings: list[str] = field(default_factory=list)

    # Operational
    latency_ms: int = 0
    input_chars: int = 0
    output_chars: int = 0

    # Faithfulness — populated by the judge
    faithfulness_score: float | None = None
    faithfulness_explanation: str | None = None


def _chunk_is_match(chunk_text: str, substrings: Sequence[str]) -> bool:
    if not substrings:
        return False
    text = chunk_text.lower()
    return all(s.lower() in text for s in substrings)


def gold_rank(record: PerQuestionRecord) -> int | None:
    """1-based rank of the first matching chunk, or None if not retrieved."""
    for i, (doc_id, text) in enumerate(
        zip(record.retrieved_doc_ids, record.retrieved_chunk_texts, strict=False), start=1
    ):
        if doc_id == record.expected_doc_id and _chunk_is_match(
            text, record.expected_chunk_substrings
        ):
            return i
    # Fall back: at least the right document showed up
    for i, doc_id in enumerate(record.retrieved_doc_ids, start=1):
        if doc_id == record.expected_doc_id:
            return i
    return None


def recall_at_k(records: list[PerQuestionRecord], k: int) -> float:
    if not records:
        return 0.0
    hits = sum(1 for r in records if (rank := gold_rank(r)) is not None and rank <= k)
    return hits / len(records)


def mean_reciprocal_rank(records: list[PerQuestionRecord]) -> float:
    if not records:
        return 0.0
    total = 0.0
    for r in records:
        rank = gold_rank(r)
        if rank is not None:
            total += 1.0 / rank
    return total / len(records)


def answer_match_rate(records: list[PerQuestionRecord]) -> float:
    if not records:
        return 0.0
    hits = 0
    for r in records:
        if not r.expected_answer_substrings:
            continue
        text = r.answer.lower()
        if any(s.lower() in text for s in r.expected_answer_substrings):
            hits += 1
    n_with_expected = sum(1 for r in records if r.expected_answer_substrings)
    return hits / n_with_expected if n_with_expected else 0.0


def mean_faithfulness(records: list[PerQuestionRecord]) -> float | None:
    scored = [r.faithfulness_score for r in records if r.faithfulness_score is not None]
    if not scored:
        return None
    return sum(scored) / len(scored)


def latency_percentiles(records: list[PerQuestionRecord]) -> dict:
    if not records:
        return {"p50_ms": 0, "p95_ms": 0, "mean_ms": 0}
    latencies = sorted(r.latency_ms for r in records)
    return {
        "p50_ms": int(statistics.median(latencies)),
        "p95_ms": int(latencies[max(0, int(0.95 * len(latencies)) - 1)]),
        "mean_ms": int(statistics.mean(latencies)),
    }


def estimated_cost(records: list[PerQuestionRecord]) -> dict:
    input_tokens = sum(r.input_chars for r in records) / CHARS_PER_TOKEN
    output_tokens = sum(r.output_chars for r in records) / CHARS_PER_TOKEN
    # Embedding cost is roughly proportional to input tokens too (one embed
    # call per question).
    embed_tokens = sum(len(r.question) for r in records) / CHARS_PER_TOKEN

    input_cost = input_tokens / 1_000_000 * COST_PER_M_INPUT_TOKENS_USD
    output_cost = output_tokens / 1_000_000 * COST_PER_M_OUTPUT_TOKENS_USD
    embed_cost = embed_tokens / 1_000_000 * COST_PER_M_EMBED_TOKENS_USD

    total = input_cost + output_cost + embed_cost
    per_query = total / len(records) if records else 0.0
    return {
        "total_usd": round(total, 6),
        "per_query_usd": round(per_query, 6),
        "breakdown": {
            "input_usd": round(input_cost, 6),
            "output_usd": round(output_cost, 6),
            "embedding_usd": round(embed_cost, 6),
        },
    }
