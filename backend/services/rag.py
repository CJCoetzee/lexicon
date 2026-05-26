"""RAG orchestration.

Composes the chunker, embedding provider, vector store, and generation
provider into two operations:

  * `index_document(document_id, name, text)` — chunk → embed → upsert
  * `answer(question, top_k)` — embed query → retrieve → prompt → generate

The orchestrator depends on Provider Protocols, not concrete classes, so
tests inject fakes and the Sprint 3 eval harness swaps providers freely.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import List

from services.chunker import ChunkConfig, chunk_text
from services.embeddings import EmbeddingProvider, get_embedding_provider
from services.llm import GenerationProvider, get_generation_provider
from services.vector_store import Chunk, RetrievalResult, VectorStore, get_vector_store

logger = logging.getLogger(__name__)


PROMPT_TEMPLATE = """You are Lexicon, a careful research assistant. Answer the user's
question using ONLY the numbered context passages below. If the answer is
not contained in the passages, say "I don't have enough information in the
provided documents to answer that."

Cite supporting passages inline using square-bracket numbers like [1], [2].
Cite multiple passages when relevant. Be concise.

CONTEXT
{context}

QUESTION
{question}

ANSWER:"""


@dataclass(frozen=True)
class Citation:
    n: int
    document_name: str
    document_id: str
    chunk_index: int
    text: str
    score: float


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    citations: List[Citation]
    latency_ms: int
    retrieved: int


class RagService:
    def __init__(
        self,
        embeddings: EmbeddingProvider | None = None,
        generation: GenerationProvider | None = None,
        store: VectorStore | None = None,
        chunk_config: ChunkConfig | None = None,
    ):
        self._embeddings = embeddings or get_embedding_provider()
        self._generation = generation or get_generation_provider()
        self._store = store or get_vector_store()
        self._chunk_config = chunk_config or ChunkConfig()

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index_document(self, document_id: str, document_name: str, text: str) -> int:
        """Chunk, embed, and store. Returns the number of chunks indexed."""
        chunks_text = chunk_text(text, self._chunk_config)
        if not chunks_text:
            return 0

        embeddings = self._embeddings.embed(chunks_text)
        chunks = [
            Chunk(
                id=f"{document_id}::{idx}",
                text=chunk,
                document_id=document_id,
                document_name=document_name,
                chunk_index=idx,
            )
            for idx, chunk in enumerate(chunks_text)
        ]
        self._store.add_chunks(chunks, embeddings)
        logger.info("Indexed %s chunks for document %s", len(chunks), document_id)
        return len(chunks)

    # ------------------------------------------------------------------
    # Retrieval + generation
    # ------------------------------------------------------------------

    def answer(self, question: str, top_k: int = 5) -> AnswerResult:
        question = question.strip()
        if not question:
            raise ValueError("question must not be empty")

        start = time.perf_counter()

        query_emb = self._embeddings.embed([question])[0]
        results = self._store.query(query_emb, top_k=top_k)

        if not results:
            return AnswerResult(
                answer=(
                    "I don't have any documents indexed yet. Upload a document "
                    "first, then ask again."
                ),
                citations=[],
                latency_ms=int((time.perf_counter() - start) * 1000),
                retrieved=0,
            )

        prompt = self._build_prompt(question, results)
        raw_answer = self._generation.generate(prompt).strip()

        cited_indices = _extract_cited_indices(raw_answer)
        citations = [
            Citation(
                n=i + 1,
                document_name=r.chunk.document_name,
                document_id=r.chunk.document_id,
                chunk_index=r.chunk.chunk_index,
                text=r.chunk.text,
                score=r.score,
            )
            for i, r in enumerate(results)
            if (i + 1) in cited_indices or not cited_indices
        ]

        return AnswerResult(
            answer=raw_answer,
            citations=citations,
            latency_ms=int((time.perf_counter() - start) * 1000),
            retrieved=len(results),
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _build_prompt(question: str, results: List[RetrievalResult]) -> str:
        context_blocks = []
        for i, result in enumerate(results, start=1):
            context_blocks.append(
                f"[{i}] (source: {result.chunk.document_name})\n{result.chunk.text}"
            )
        context = "\n\n".join(context_blocks)
        return PROMPT_TEMPLATE.format(context=context, question=question)


_CITATION_RE = re.compile(r"\[(\d+)\]")


def _extract_cited_indices(answer: str) -> set[int]:
    return {int(m.group(1)) for m in _CITATION_RE.finditer(answer)}


_singleton: RagService | None = None


def get_rag_service() -> RagService:
    global _singleton
    if _singleton is None:
        _singleton = RagService()
    return _singleton
