"""Tests for the LLM-as-judge faithfulness scorer.

We pass a fake generator so these tests are deterministic and offline.
"""
from __future__ import annotations

from eval.judge import FaithfulnessJudge, _parse


class FakeGen:
    def __init__(self, output: str):
        self.output = output

    def generate(self, prompt: str) -> str:
        return self.output


def test_judge_parses_clean_json():
    judge = FaithfulnessJudge(generation=FakeGen('{"score": 0.9, "reason": "supported"}'))
    result = judge.score("q", "a", ["chunk"])
    assert result.score == 0.9
    assert "supported" in result.reason


def test_judge_clamps_score_to_unit_interval():
    judge = FaithfulnessJudge(generation=FakeGen('{"score": 1.5, "reason": "too high"}'))
    assert judge.score("q", "a", ["c"]).score == 1.0
    judge = FaithfulnessJudge(generation=FakeGen('{"score": -0.2, "reason": "too low"}'))
    assert judge.score("q", "a", ["c"]).score == 0.0


def test_judge_extracts_json_from_code_fence():
    fenced = '```json\n{"score": 0.5, "reason": "ok"}\n```'
    result = _parse(fenced)
    assert result.score == 0.5


def test_judge_returns_zero_on_unparseable_output():
    result = _parse("Not JSON at all.")
    assert result.score == 0.0
    assert "unparseable" in result.reason


def test_judge_handles_malformed_json():
    result = _parse('{"score": "high", "reason": "bad type"}')
    assert result.score == 0.0
