"""Generation service.

Wraps the Gemini chat model. Sprint 2 will add the actual RAG prompt and
citation handling; Sprint 1 ships the bare client so the module exists and
can be imported without crashing.
"""
from __future__ import annotations

import logging
from typing import Protocol

from google import genai

from config import config

logger = logging.getLogger(__name__)


class GenerationProvider(Protocol):
    def generate(self, prompt: str) -> str: ...


class GeminiGenerationProvider:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._client = genai.Client(api_key=api_key or config.gemini_api_key)
        self._model = model or config.generation_model

    def generate(self, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
        )
        return response.text or ""


_singleton: GenerationProvider | None = None


def get_generation_provider() -> GenerationProvider:
    global _singleton
    if _singleton is None:
        _singleton = GeminiGenerationProvider()
    return _singleton
