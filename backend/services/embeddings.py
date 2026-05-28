"""Embedding service.

Wraps the Gemini embedding model behind a small interface so we can swap
providers (or fall back to a local sentence-transformers model) without
touching call sites. Sprint 1 ships the Gemini adapter; Sprint 3's eval
harness will use the same interface to A/B against alternatives.
"""
from __future__ import annotations

import logging
from typing import Protocol

from google import genai

from config import config

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    """Anything that can turn a list of strings into vectors."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class GeminiEmbeddingProvider:
    """Embeddings via Google's Gemini embedding endpoint.

    Default model: `gemini-embedding-001`. Free tier quotas are generous
    enough for development and demos. The model produces high-dimensional
    embeddings well-suited to RAG retrieval.

    Some embedding endpoints reject very large batches; we chunk requests
    into `BATCH_LIMIT`-sized groups to be safe across model versions.
    """

    BATCH_LIMIT = 100

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._client = genai.Client(api_key=api_key or config.gemini_api_key)
        self._model = model or config.embedding_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), self.BATCH_LIMIT):
            batch = texts[i : i + self.BATCH_LIMIT]
            result = self._client.models.embed_content(
                model=self._model,
                contents=batch,
            )
            all_embeddings.extend(list(item.values) for item in result.embeddings)
        return all_embeddings


_singleton: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Lazy singleton — avoids constructing the client at import time."""
    global _singleton
    if _singleton is None:
        _singleton = GeminiEmbeddingProvider()
    return _singleton
