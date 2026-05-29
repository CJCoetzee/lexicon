"""RAG orchestration.

Composes the chunker, embedding provider, vector store, optional reranker,
and generation provider into three operations:

  * index_document(...) -- chunk, embed, upsert
  * answer(...)         -- non-streaming Q&A with citations
  * answer_stream(...)  -- streaming Q&A yielding token + done events

All providers are injected as Protocols so tests use fakes and the eval
harness can swap implementations.
"""
from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass

from services.chunker import ChunkConfig, chunk_text
from services.embeddings import EmbeddingProvider, get_embedding_provider
from services.llm import GenerationProvider, get_generation_provider
from services.reranker import Reranker
from services.vector_store import Chunk, RetrievalResult, VectorStore, get_vector_store

logger = logging.getLogger(__name__)


PROMPT_TEMPLATE = """You are Lexicon, a careful research assistant. Answer
the user's question using ONLY the numbered context passages below. If the
answer is not contained in the passages, say "I don't have enough
information in the provided documents to answer that."

Cite supporting passages inline using square-bracket numbers like [1], [2].
Cite multiple passages when relevant. Be concise. Take prior turns of the
conversation into account when interpreting follow-up questions.

CONTEXT
{context}
{history_block}
CURRENT QUESTION
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
    citations: list[Citation]
    latency_ms: int
    retrieved: int


class RagService:
    def __init__(
        self,
        embeddings: EmbeddingProvider | None = None,
        generation: GenerationProvider | None = None,
        store: VectorStore | None = None,
        chunk_config: ChunkConfig | None = None,
        reranker: Reranker | None = None,
        retrieval_overfetch: int = 2,
    ):
        self._embeddings = embeddings or get_embedding_provider()
        self._generation = generation or get_generation_provider()
        self._store = store or get_vector_store()
        self._chunk_config = chunk_config or ChunkConfig()
        self._reranker = reranker
        self._retrieval_overfetch = max(1, retrieval_overfetch)

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index_document(self, document_id: str, document_name: str, text: str) -> int:
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
    # Answer (non-streaming)
    # ------------------------------------------------------------------

    def answer(
        self,
        question: str,
        top_k: int = 5,
        history: list[dict] | None = None,
    ) -> AnswerResult:
        question = question.strip()
        if not question:
            raise ValueError("question must not be empty")

        start = time.perf_counter()
        results = self._retrieve(question, top_k)

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

        prompt = self._build_prompt(question, results, history)
        raw_answer = self._generation.generate(prompt).strip()
        citations = _citations_from(results, raw_answer)

        return AnswerResult(
            answer=raw_answer,
            citations=citations,
            latency_ms=int((time.perf_counter() - start) * 1000),
            retrieved=len(results),
        )

    # ------------------------------------------------------------------
    # Answer (streaming)
    # ------------------------------------------------------------------

    def answer_stream(
        self,
        question: str,
        top_k: int = 5,
        history: list[dict] | None = None,
    ):
        question = question.strip()
        if not question:
            raise ValueError("question must not be empty")

        start = time.perf_counter()
        results = self._retrieve(question, top_k)

        if not results:
            msg = ("I don't have any documents indexed yet. Upload a document "
                   "first, then ask again.")
            yield {"type": "token", "text": msg}
            yield {
                "type": "done",
                "citations": [],
                "latency_ms": int((time.perf_counter() - start) * 1000),
                "retrieved": 0,
            }
            return

        prompt = self._build_prompt(question, results, history)

        buffer: list[str] = []
        for chunk in self._generation.generate_stream(prompt):
            buffer.append(chunk)
            yield {"type": "token", "text": chunk}

        full_answer = "".join(buffer).strip()
        citations = _citations_from(results, full_answer)
        yield {
            "type": "done",
            "citations": [
                {
                    "n": c.n,
                    "document_name": c.document_name,
                    "document_id": c.document_id,
                    "chunk_index": c.chunk_index,
                    "text": c.text,
                    "score": c.score,
                }
                for c in citations
            ],
            "latency_ms": int((time.perf_counter() - start) * 1000),
            "retrieved": len(results),
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _retrieve(self, question: str, top_k: int) -> list[RetrievalResult]:
        query_emb = self._embeddings.embed([question])[0]
        fetch_k = top_k * self._retrieval_overfetch if self._reranker else top_k
        results = self._store.query(query_emb, top_k=fetch_k)
        if self._reranker and results:
            scored = self._reranker.rerank(question, results)
            results = [s.result for s in scored[:top_k]]
        return results

    @staticmethod
    def _build_prompt(
        question: str,
        results: list[RetrievalResult],
        history: list[dict] | None = None,
    ) -> str:
        context_blocks = []
        for i, result in enumerate(results, start=1):
            context_blocks.append(
                f"[{i}] (source: {result.chunk.document_name})\n{result.chunk.text}"
            )
        context = "\n\n".join(context_blocks)

        history_block = ""
        if history:
            lines: list[str] = []
            for turn in history[-6:]:  # cap to last 6 turns
                role = (turn.get("role") or "").lower()
                text = (turn.get("text") or "").strip()
                if not text:
                    continue
                if role == "user":
                    lines.append(f"User: {text}")
                elif role == "assistant":
                    lines.append(f"Assistant: {text}")
            if lines:
                history_block = "\nCONVERSATION SO FAR\n" + "\n".join(lines) + "\n"

        return PROMPT_TEMPLATE.format(
            context=context, history_block=history_block, question=question
        )


_CITATION_RE = re.compile(r"\[(\d+)\]")


def _extract_cited_indices(answer: str) -> set[int]:
    return {int(m.group(1)) for m in _CITATION_RE.finditer(answer)}


def _citations_from(
    results: list[RetrievalResult], answer_text: str
) -> list[Citation]:
    cited_indices = _extract_cited_indices(answer_text)
    return [
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


_singleton: RagService | None = None


def get_rag_service() -> RagService:
    global _singleton
    if _singleton is None:
        _singleton = RagService()
    return _singleton
