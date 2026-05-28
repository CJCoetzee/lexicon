"""Vector store service.

Thin wrapper around Chroma's PersistentClient. The wrapper exposes only the
operations Lexicon needs (add chunks, query top-k) which makes the surface
small enough to mock in tests and easy to swap for pgvector or Pinecone later
without rewriting call sites.

Sprint 1 only initialises the client; Sprint 2 implements add/query.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

import chromadb
from chromadb.config import Settings

from config import config

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "lexicon_documents"


@dataclass(frozen=True)
class Chunk:
    """A single retrievable text chunk."""

    id: str
    text: str
    document_id: str
    document_name: str
    chunk_index: int


@dataclass(frozen=True)
class RetrievalResult:
    chunk: Chunk
    score: float


class VectorStore:
    """Chroma-backed vector store, wrapped behind a small interface.

    We pass embeddings in explicitly rather than letting Chroma call the
    embedding function for us. This makes the embedding choice an explicit,
    testable boundary — and lets the eval harness in Sprint 3 swap providers.
    """

    def __init__(self, persist_dir: str | None = None):
        self._persist_dir = persist_dir or config.chroma_persist_dir
        os.makedirs(self._persist_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=self._persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "Vector store initialised at %s (collection=%s, count=%s)",
            self._persist_dir,
            _COLLECTION_NAME,
            self._collection.count(),
        )

    # ------------------------------------------------------------------
    # Sprint 2 will fill in the real implementations.
    # We provide stubs so the module is importable in Sprint 1.
    # ------------------------------------------------------------------

    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must be the same length")
        self._collection.add(
            ids=[c.id for c in chunks],
            documents=[c.text for c in chunks],
            embeddings=embeddings,
            metadatas=[
                {
                    "document_id": c.document_id,
                    "document_name": c.document_name,
                    "chunk_index": c.chunk_index,
                }
                for c in chunks
            ],
        )

    def query(self, embedding: list[float], top_k: int = 5) -> list[RetrievalResult]:
        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        results: list[RetrievalResult] = []
        for chunk_id, text, meta, distance in zip(ids, documents, metadatas, distances, strict=False):
            results.append(
                RetrievalResult(
                    chunk=Chunk(
                        id=chunk_id,
                        text=text,
                        document_id=meta.get("document_id", ""),
                        document_name=meta.get("document_name", ""),
                        chunk_index=int(meta.get("chunk_index", 0)),
                    ),
                    # cosine distance in [0,2]; convert to similarity in [-1,1]
                    score=1.0 - float(distance),
                )
            )
        return results

    def count(self) -> int:
        return self._collection.count()

    def reset(self) -> None:
        """Wipe the collection. Used by tests; never exposed via the API."""
        self._client.delete_collection(_COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )


_singleton: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _singleton
    if _singleton is None:
        _singleton = VectorStore()
    return _singleton
