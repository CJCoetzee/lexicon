"""Eval runner.

Indexes a dataset's documents into an isolated Chroma collection, runs every
question through the RAG pipeline, computes metrics, and writes a JSON report.

Usage:
    python -m eval.runner --dataset eval/datasets/example.json --out eval/reports/baseline.json
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

# Allow `python -m eval.runner` from the backend/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chromadb  # noqa: E402,I001
from chromadb.config import Settings  # noqa: E402

from config import config  # noqa: E402
from eval.dataset import EvalDataset, load_dataset  # noqa: E402
from eval.judge import FaithfulnessJudge  # noqa: E402
from eval.metrics import (  # noqa: E402
    PerQuestionRecord,
    answer_match_rate,
    estimated_cost,
    latency_percentiles,
    mean_faithfulness,
    mean_reciprocal_rank,
    recall_at_k,
)
from services.embeddings import get_embedding_provider  # noqa: E402
from services.llm import get_generation_provider  # noqa: E402
from services.rag import RagService  # noqa: E402
from services.reranker import GeminiReranker  # noqa: E402
from services.vector_store import VectorStore  # noqa: E402

logger = logging.getLogger("eval.runner")


@dataclass
class RunConfig:
    dataset_path: str
    output_path: str
    top_k: int = 5
    rerank: bool = False
    judge: bool = True
    limit: int = 0


def _build_isolated_rag(persist_dir: str, rerank: bool = False) -> RagService:
    """Build a RagService backed by a fresh Chroma collection on disk.

    We don't use the singleton because the eval should not pollute the live
    production collection.
    """
    collection_name = f"eval_{int(time.time() * 1000)}"

    class _IsolatedVectorStore(VectorStore):
        def __init__(self):
            import os
            self._persist_dir = persist_dir
            os.makedirs(self._persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self._persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    reranker = GeminiReranker() if rerank else None
    return RagService(
        embeddings=get_embedding_provider(),
        generation=get_generation_provider(),
        store=_IsolatedVectorStore(),
        reranker=reranker,
    )


def run(cfg: RunConfig) -> dict:
    dataset: EvalDataset = load_dataset(cfg.dataset_path)
    print(f"Loaded dataset '{dataset.name}' "
          f"({len(dataset.documents)} docs, {len(dataset.questions)} questions)")

    import tempfile
    with tempfile.TemporaryDirectory(prefix="lexicon_eval_") as tmpdir:
        rag = _build_isolated_rag(tmpdir, rerank=cfg.rerank)

        for doc in dataset.documents:
            n = rag.index_document(doc.id, doc.name, doc.content)
            print(f"  indexed {doc.id} -> {n} chunks")

        questions = dataset.questions[: cfg.limit] if cfg.limit > 0 else dataset.questions
        records: list[PerQuestionRecord] = []
        for i, q in enumerate(questions, start=1):
            t0 = time.perf_counter()
            answer_result = rag.answer(q.question, top_k=cfg.top_k)
            latency_ms = int((time.perf_counter() - t0) * 1000)

            retrieved_doc_ids: list[str] = []
            retrieved_chunk_texts: list[str] = []
            for citation in answer_result.citations:
                retrieved_doc_ids.append(citation.document_id)
                retrieved_chunk_texts.append(citation.text)

            input_chars = sum(len(t) for t in retrieved_chunk_texts) + len(q.question)
            record = PerQuestionRecord(
                question=q.question,
                expected_doc_id=q.expected_doc_id,
                retrieved_doc_ids=retrieved_doc_ids,
                retrieved_chunk_texts=retrieved_chunk_texts,
                expected_chunk_substrings=q.expected_chunk_substrings,
                answer=answer_result.answer,
                expected_answer_substrings=q.expected_answer_substrings,
                latency_ms=latency_ms,
                input_chars=input_chars,
                output_chars=len(answer_result.answer),
            )

            if cfg.judge:
                judge = FaithfulnessJudge()
                judge_result = judge.score(
                    q.question, answer_result.answer, retrieved_chunk_texts
                )
                record.faithfulness_score = judge_result.score
                record.faithfulness_explanation = judge_result.reason

            records.append(record)
            faith = record.faithfulness_score if record.faithfulness_score is not None else "-"
            print(f"  [{i}/{len(questions)}] {latency_ms:>5} ms . "
                  f"rank={_rank_or_dash(record)} . faith={faith}")

        report = _build_report(dataset, cfg, records)

    out = Path(cfg.output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nReport written to {out}\n")
    _print_summary(report)
    return report


def _rank_or_dash(record: PerQuestionRecord) -> str:
    from eval.metrics import gold_rank
    r = gold_rank(record)
    return str(r) if r is not None else "-"


def _build_report(dataset: EvalDataset, cfg: RunConfig, records: list[PerQuestionRecord]) -> dict:
    return {
        "metadata": {
            "dataset": dataset.name,
            "run_at": datetime.now(UTC).isoformat(),
            "config": {
                "top_k": cfg.top_k,
                "rerank": cfg.rerank,
                "judge": cfg.judge,
                "limit": cfg.limit,
                "generation_model": config.generation_model,
                "embedding_model": config.embedding_model,
            },
            "n_questions": len(records),
        },
        "metrics": {
            "recall_at_1": recall_at_k(records, 1),
            "recall_at_3": recall_at_k(records, 3),
            "recall_at_5": recall_at_k(records, 5),
            "mrr": mean_reciprocal_rank(records),
            "answer_substring_match_rate": answer_match_rate(records),
            "faithfulness_mean": mean_faithfulness(records),
            "latency": latency_percentiles(records),
            "cost": estimated_cost(records),
        },
        "records": [asdict(r) for r in records],
    }


def _print_summary(report: dict) -> None:
    m = report["metrics"]
    print("Metrics summary:")
    print(f"  recall@1            : {m['recall_at_1']:.2%}")
    print(f"  recall@3            : {m['recall_at_3']:.2%}")
    print(f"  recall@5            : {m['recall_at_5']:.2%}")
    print(f"  MRR                 : {m['mrr']:.3f}")
    print(f"  answer match rate   : {m['answer_substring_match_rate']:.2%}")
    if m["faithfulness_mean"] is not None:
        print(f"  faithfulness (mean) : {m['faithfulness_mean']:.3f}")
    print(f"  latency p50 / p95   : {m['latency']['p50_ms']} / {m['latency']['p95_ms']} ms")
    print(f"  est. cost per query : ${m['cost']['per_query_usd']:.6f}")


def _parse_args(argv: list[str]) -> RunConfig:
    p = argparse.ArgumentParser(description="Run the Lexicon RAG eval.")
    p.add_argument("--dataset", required=True, help="Path to dataset JSON.")
    p.add_argument("--out", required=True, help="Path to output report JSON.")
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--rerank", action="store_true")
    p.add_argument("--no-judge", action="store_true",
                   help="Skip LLM-as-judge faithfulness (saves API calls).")
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args(argv)
    return RunConfig(
        dataset_path=args.dataset,
        output_path=args.out,
        top_k=args.top_k,
        rerank=args.rerank,
        judge=not args.no_judge,
        limit=args.limit,
    )


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING)
    cfg = _parse_args(argv or sys.argv[1:])
    run(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
