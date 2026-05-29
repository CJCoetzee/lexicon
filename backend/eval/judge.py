"""LLM-as-judge faithfulness scoring."""
from __future__ import annotations

import json
import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass

from services.llm import GenerationProvider, get_generation_provider

logger = logging.getLogger(__name__)


_PROMPT = """You are a strict evaluator. Score the answer for FAITHFULNESS
to the provided context -- is every factual claim in the answer supported
by at least one passage?

Return ONLY a single JSON object on one line:
{{"score": <float between 0 and 1>, "reason": "<one short sentence>"}}

A score of 1.0 means every claim is supported. 0.0 means the answer
contradicts or invents content not in the passages. An answer of
"I don't have enough information..." against passages that DON'T
contain the answer is a faithful response and should score 1.0.

QUESTION
{question}

PASSAGES
{context}

ANSWER
{answer}

YOUR JSON:"""


@dataclass(frozen=True)
class JudgeResult:
    score: float
    reason: str


class FaithfulnessJudge:
    def __init__(self, generation: GenerationProvider | None = None):
        self._generation = generation or get_generation_provider()

    def score(self, question: str, answer: str, chunks: Sequence[str]) -> JudgeResult:
        context = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(chunks))
        prompt = _PROMPT.format(question=question, context=context, answer=answer)
        raw = self._generation.generate(prompt).strip()
        return _parse(raw)


def _parse(raw: str) -> JudgeResult:
    match = re.search(r"\{.*?\}", raw, re.DOTALL)
    if not match:
        logger.warning("Judge returned non-JSON output: %r", raw[:200])
        return JudgeResult(score=0.0, reason="unparseable judge output")
    try:
        obj = json.loads(match.group(0))
        score = float(obj.get("score", 0.0))
        score = max(0.0, min(1.0, score))
        reason = str(obj.get("reason", "")).strip()
        return JudgeResult(score=score, reason=reason)
    except (json.JSONDecodeError, ValueError, TypeError) as exc:
        logger.warning("Judge JSON parse failed: %s -- raw: %r", exc, raw[:200])
        return JudgeResult(score=0.0, reason="unparseable judge output")
