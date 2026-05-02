"""Embedding service.

Wraps the Gemini embedding model behind a small interface so we can swap
providers (or fall back to a local sentence-transformers model) without
touching call sites. Sprint 1 ships the Gemini adapter; Sprint 3's eval
harness will use the same interface to A/B against alternatives.
"""
from __future__ import annotations

import logging
from typing import List, Protocol

from google import genai

from config import config

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    """Anything that can turn a list of strings into vectors."""

    def embed(self, texts: List[str]) -> List[List[float]]: ...


class GeminiEmbeddingProvider:
    """Embeddings via Google `text-embedding-004`.

    Free tier quotas (as of 2025): generous enough for development and demos.
    The model produces 768-dimensional vectors.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._client = genai.Client(api_key=api_key or config.gemini_api_key)
        self._model = model or config.embedding_model

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        result = self._client.models.embed_content(
            model=self._model,
            contents=texts,
        )
        # The new SDK returns an object with .embeddings, each having .values.
        return [list(item.values) for item in result.embeddings]


_singleton: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Lazy singleton — avoids constructing the client at import time."""
    global _singleton
    if _singleton is None:
        _singleton = GeminiEmbeddingProvider()
    return _singleton
