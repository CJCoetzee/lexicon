"""Suggested-question generation.

After a user uploads a document, the empty chat input is a UX cold start —
they have to think of a question. This service asks the LLM to propose three
short, document-grounded questions a user might want to ask.

It's a single Gemini call per upload; failures are non-fatal (the upload
returns an empty list of suggestions and the UI handles it).
"""
from __future__ import annotations

import json
import logging
import re

from services.llm import GenerationProvider, get_generation_provider

logger = logging.getLogger(__name__)


_PROMPT = """You are helping a user start a conversation about a document
they just uploaded. Read the document text below and propose THREE short,
specific questions a curious reader could ask. Each question must be
answerable from the document itself (no outside knowledge).

Return ONLY a JSON array of strings on a single line. No prose, no code
fences. Example shape: ["Question one?", "Question two?", "Question three?"]

DOCUMENT
{excerpt}

YOUR JSON:"""


# Cap the prompt-context excerpt to keep token cost bounded even for huge
# documents. The first ~2000 chars are usually enough signal.
_EXCERPT_LIMIT = 2000


def generate_suggested_questions(
    document_text: str,
    generation: GenerationProvider | None = None,
) -> list[str]:
    if not document_text or not document_text.strip():
        return []
    gen = generation or get_generation_provider()
    excerpt = document_text[:_EXCERPT_LIMIT]
    try:
        raw = gen.generate(_PROMPT.format(excerpt=excerpt)).strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Suggested-question generation failed: %s", exc)
        return []
    return _parse(raw)


def _parse(raw: str) -> list[str]:
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        return []
    try:
        arr = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    out: list[str] = []
    for item in arr:
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned:
                out.append(cleaned)
    return out[:3]
