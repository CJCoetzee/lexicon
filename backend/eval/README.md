# Lexicon RAG eval harness

A small, honest evaluation harness for the Lexicon RAG pipeline. Inputs a
JSON dataset of (documents, questions, expected substrings); outputs a JSON
report with retrieval recall@k, MRR, LLM-as-judge faithfulness, latency
percentiles, and an estimated cost-per-query.

## Why this exists

The capstone deliverable is "an AI system" — but anyone can plumb together
an LLM API. The thing that turns this into an ML-engineering project is
having an *honest measurement* of how well the system works and using that
measurement to iterate (Sprint 3's reranker is a direct response to what we
saw here).

## Dataset format

`backend/eval/datasets/<name>.json`:

```json
{
  "name": "example",
  "documents": [
    {"id": "wikipedia-france", "name": "France.txt", "content": "France is a country in Western Europe..."}
  ],
  "questions": [
    {
      "question": "What is the capital of France?",
      "expected_doc_id": "wikipedia-france",
      "expected_chunk_substrings": ["capital", "Paris"],
      "expected_answer_substrings": ["Paris"]
    }
  ]
}
```

`expected_chunk_substrings` are used for retrieval recall: a retrieved
chunk counts as "correct" if it contains *all* of them.
`expected_answer_substrings` are used for a deterministic faithfulness
sanity check before falling back to LLM-as-judge.

## Running

```bash
cd backend
python -m eval.runner --dataset eval/datasets/example.json --out eval/reports/baseline.json
```

Optional flags:

| Flag           | Default | What it does                                      |
|----------------|---------|---------------------------------------------------|
| `--top-k`      | 5       | k for recall@k                                    |
| `--rerank`     | false   | Enable Gemini reranker (Sprint 3 improvement)     |
| `--judge`      | true    | Run LLM-as-judge faithfulness scoring             |
| `--limit`      | 0       | If >0, only run the first N questions             |

## Metrics

- **recall@k** — fraction of questions where the gold chunk is in the top-k.
- **MRR** — mean reciprocal rank of the gold chunk across the top-k.
- **faithfulness** — LLM-as-judge score 0-1 over (question, answer, context).
- **answer_match** — deterministic check: does the answer contain *any* of
  `expected_answer_substrings`?
- **latency_ms** — p50, p95 of end-to-end answer latency.
- **est_cost_usd** — rough cost estimate using public Gemini Flash pricing.

## Reports

Reports are saved as JSON. The Sprint 3 demo will compare `baseline.json`
against `reranked.json` to demonstrate the iteration.
