"""Gemini-as-reranker.

Vector similarity is fast but coarse — it ranks by overall semantic
closeness, not by whether a chunk actually contains the answer. A small
follow-up LLM pass that *reads* each candidate and scores its relevance
typically lifts recall@k materially for the cost of one extra API call.

This module implements a single-call listwise reranker: given the question
and the top-k chunks, it asks Gemini to score each on a 0–10 scale and
returns the chunks sorted by descending score. The Sprint 3 eval report
will compare baseline-only vs. baseline+rerank to quantify the lift.
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import List, Protocol

from services.llm import GenerationProvider, get_generation_provider
from services.vector_store import RetrievalResult

logger = logging.getLogger(__name__)


_PROMPT = """You are scoring passages for relevance to a user's question.

For each numbered passage below, return a JSON array on a single line of
the form:
  [{{"n": 1, "score": 8.5}}, {{"n": 2, "score": 1.0}}, ...]

Score range: 0 (irrelevant) to 10 (directly answers the question). Use
the full range; do not flatten to all-10s. Output the JSON array ONLY,
no prose, no code fences.

QUESTION
{question}

PASSAGES
{passages}

YOUR JSON:"""


@dataclass(frozen=True)
class ScoredChunk:
    result: RetrievalResult
    rerank_score: float


class Reranker(Protocol):
    def rerank(
        self, question: str, results: List[RetrievalResult]
    ) -> List[ScoredChunk]: ...


class GeminiReranker:
    def __init__(self, generation: GenerationProvider | None = None):
        self._generation = generation or get_generation_provider()

    def rerank(
        self, question: str, results: List[RetrievalResult]
    ) -> List[ScoredChunk]:
        if not results:
            return []
        passages = "\n\n".join(
            f"[{i + 1}] {r.chunk.text}" for i, r in enumerate(results)
        )
        prompt = _PROMPT.format(question=question, passages=passages)
        raw = self._generation.generate(prompt).strip()
        scores = _parse_scores(raw, expected_n=len(results))

        scored = [
            ScoredChunk(result=r, rerank_score=scores.get(i + 1, 0.0))
            for i, r in enumerate(results)
        ]
        scored.sort(key=lambda s: s.rerank_score, reverse=True)
        return scored


def _parse_scores(raw: str, expected_n: int) -> dict[int, float]:
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        logger.warning("Reranker returned non-array output: %r", raw[:200])
        return {}
    try:
        arr = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        logger.warning("Reranker JSON parse failed: %s — raw: %r", exc, raw[:200])
        return {}

    out: dict[int, float] = {}
    for item in arr:
        try:
            n = int(item["n"])
            score = float(item["score"])
        except (KeyError, ValueError, TypeError):
            continue
        if 1 <= n <= expected_n:
            out[n] = max(0.0, min(10.0, score))
    return out
