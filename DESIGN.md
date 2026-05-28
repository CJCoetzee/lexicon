# Lexicon — Design and Testing Document

This document explains the architecture, design decisions, and testing
strategy for Lexicon, the MSSE Capstone project. It satisfies the rubric
requirement that the repository "include a detailed design and testing
document listing and explaining design and architecture decisions made,
including any software and architectural patterns used, and details of
software testing implemented."

> **Status:** This document is updated incrementally as the project evolves.
> Sprint 1 sections are complete; Sprint 2 and Sprint 3 sections will fill
> in as those sprints land.

---

## 1. Problem statement

Researchers, students, and analysts spend significant time finding specific
answers buried in long documents — papers, reports, manuals. Existing search
returns pages, not answers, and rarely cites which paragraph supports the
claim. Lexicon lets a user upload a set of documents and ask natural-language
questions, returning a synthesised answer with inline citations to the source
passages.

## 2. High-level architecture

```
   ┌──────────────────────────┐         ┌────────────────────────────┐
   │  React frontend (Vite)   │         │   Flask backend (Python)   │
   │                          │  HTTPS  │                            │
   │  • Upload drop-zone      │ ──────▶ │  /api/documents  (upload)  │
   │  • Document list         │         │  /api/chat       (Sprint 2)│
   │  • Chat panel            │ ◀────── │                            │
   └──────────────────────────┘         └─────────────┬──────────────┘
                                                       │
                                  ┌────────────────────┼─────────────────────┐
                                  │                    │                     │
                          ┌───────▼──────┐    ┌────────▼────────┐    ┌──────▼──────┐
                          │ Document     │    │ Embeddings      │    │ Chroma      │
                          │ parser       │    │ (Gemini API)    │    │ vector DB   │
                          │ (pypdf/text) │    │                 │    │ (persistent)│
                          └──────────────┘    └────────┬────────┘    └──────┬──────┘
                                                       │                     │
                                              ┌────────▼─────────────────────▼──────┐
                                              │ Generation (Gemini API) — RAG prompt│
                                              └──────────────────────────────────────┘
```

The system follows a classic three-tier shape: presentation (React),
application (Flask), and data (Chroma + uploaded documents on disk). The
Flask layer composes three independent services — parsing, embeddings,
generation — around a vector store that persists the index across restarts.

## 3. Architectural and design patterns

### 3.1 Application factory (Flask)
`backend/app.py` exposes `create_app()` rather than instantiating a single
global `Flask` object. This is the canonical Flask pattern and lets us build
isolated app instances for tests, dev, and prod without state leakage. It
also keeps the WSGI entry point (`gunicorn 'app:create_app()'`) trivial.

### 3.2 Strategy pattern (document parser)
`services/parser.py` keeps a registry mapping file extension → extractor
function. Adding a new format (e.g. `.docx`, `.html`) is a one-line change to
the registry and a new extractor function — no call sites change. This is
the Strategy pattern in its smallest, most useful form.

### 3.3 Provider Protocols (embeddings, generation)
`services/embeddings.py` and `services/llm.py` define `Protocol` types
(`EmbeddingProvider`, `GenerationProvider`) and a Gemini implementation. This
is the Adapter / Strategy pattern: swapping to a local sentence-transformers
embedder, an Anthropic Claude generator, or a Groq Llama generator is a
single-class change that doesn't touch route code or tests. The Sprint 3 eval
harness will exploit this directly to A/B providers.

### 3.4 Repository / facade (vector store)
`services/vector_store.py` exposes only the four operations Lexicon needs —
`add_chunks`, `query`, `count`, `reset` — over the larger Chroma surface.
This Facade pattern makes the wrapper testable and makes a future migration
to pgvector / Pinecone a swap of one class.

### 3.5 Lazy singletons
`get_embedding_provider`, `get_generation_provider`, and `get_vector_store`
return module-level lazy singletons. This avoids instantiating the Gemini
client (or hitting disk for Chroma) at import time, which keeps unit tests
fast and avoids requiring `GEMINI_API_KEY` to merely load a module.

## 4. Technology choices

| Concern        | Choice                       | Why                                                                                     |
|----------------|------------------------------|-----------------------------------------------------------------------------------------|
| Backend lang   | Python 3.11                  | Strong ML/embedding ecosystem; matches the project's ML-engineering framing.            |
| Web framework  | Flask                        | Minimal, well-understood, fits the API-only backend we need.                            |
| Frontend       | React + Vite + Tailwind      | Fast dev loop; Tailwind keeps styling co-located without bespoke CSS files.             |
| Vector store   | Chroma (embedded)            | Zero infra, persistent on disk, free-tier-deployable. Good enough for a capstone-scale corpus. |
| Embeddings     | Gemini `gemini-embedding-001`| Free tier, high-quality embeddings. Provider-Protocol design lets the eval harness A/B against local sentence-transformers. |
| LLM            | Gemini `gemini-2.5-flash-lite` | Free-tier-friendly Gemini variant, fast, low cost. Provider-Protocol lets us swap.    |
| Hosting        | Render (free tier)           | One-click GitHub deploy, supports Python web services + static React, persistent disk.  |
| CI/CD          | GitHub Actions               | Free for public repos, native to GitHub, runs on every PR.                              |

### Cost analysis

The free tier covers all expected demo usage. If the project were promoted
to a paid tier:

- **Gemini Flash:** ~$0.075/1M input tokens, ~$0.30/1M output. A heavy user
  asking 50 questions/day with 8K context would cost roughly $0.30/month.
- **Render Starter:** $7/month per service (backend + frontend). Or use
  Render's free tier indefinitely if uptime gaps are acceptable.
- **Self-hosted alternative:** A 2 vCPU / 2 GB VPS at ~$5/month plus
  swapping Gemini for a local Llama-3-8B via Ollama — zero per-request cost
  but lower answer quality and higher operational overhead.

For a production deployment we would recommend the cloud option with
Render Starter ($14/month) or a similar PaaS over self-hosting, on the
grounds that the operational burden of patching, monitoring, and securing
a VPS dwarfs the cost difference for a small-scale internal tool.

## 5. Data flow

### 5.1 Upload (Sprint 1, complete)
1. User drops a PDF/TXT/MD file in the React `UploadZone`.
2. Frontend POSTs `multipart/form-data` to `POST /api/documents`.
3. Flask resolves the extractor by extension and runs it.
4. Server returns a JSON document descriptor (`id`, `filename`, `char_count`,
   `preview`, `uploaded_at`).
5. Frontend prepends the descriptor to the visible document list.

### 5.2 Indexing and chat (Sprint 2, complete)
On upload, the document text is chunked using a recursive character splitter
(`services/chunker.py`) that prefers paragraph and sentence boundaries over
arbitrary mid-word cuts. Chunks default to 600 characters with 100-character
overlap; the configuration is a `ChunkConfig` dataclass that the Sprint 3
eval harness will sweep over.

Each chunk is embedded via Gemini `text-embedding-004` and added to Chroma
with metadata linking it back to its document and original chunk index.
Indexing happens inline on upload — fine for capstone-scale corpora and
honest about user-perceived latency. A future improvement (a job queue with
a background worker) is noted in Section 9.

For a chat query the flow is:

1. Embed the question (single Gemini call).
2. Query Chroma for the top-k nearest chunks (cosine).
3. Build a prompt with `[1]`, `[2]` numbered context blocks and explicit
   instructions to cite inline and refuse out-of-scope questions.
4. Generate via `gemini-1.5-flash`.
5. Parse `[n]` markers out of the answer; return only those citations the
   model actually referenced (falls back to all retrieved chunks if the
   model emits no markers).

Latency is reported back to the client per-call so the UI can surface it.

### 5.3 Evaluation (Sprint 3, complete)
Lives in `backend/eval/` and runs offline against a JSON dataset of
(documents, questions, expected substrings). The runner:

1. Spins up an isolated Chroma collection in a `TemporaryDirectory` so the
   live production index is never touched.
2. Indexes the dataset's documents using the same `RagService.index_document`
   path used in production — same chunker, same embeddings.
3. Runs every question through `RagService.answer`, recording the retrieved
   chunks, answer, and latency per question.
4. Optionally runs an **LLM-as-judge** faithfulness scorer (`eval/judge.py`)
   that asks Gemini, with the question + retrieved context + answer, to
   produce a JSON faithfulness score on 0–1.
5. Computes summary metrics (`eval/metrics.py`) — recall@1/3/5, MRR,
   answer-substring match rate, mean faithfulness, p50/p95 latency, and an
   estimated USD cost using Gemini Flash pricing constants.
6. Writes a JSON report to `eval/reports/<name>.json`.

```
python -m eval.runner --dataset eval/datasets/example.json --out eval/reports/baseline.json
python -m eval.runner --dataset eval/datasets/example.json --out eval/reports/reranked.json --rerank
```

A diff between baseline and reranked reports is the central artifact of
Section 5.4.

### 5.4 Retrieval improvement: Gemini-as-reranker (Sprint 3, complete)
Vector similarity is fast but coarse. Implemented `services/reranker.py`,
a listwise reranker that:

1. Receives the top-k chunks from the embedding retriever (overfetched by a
   configurable factor — default 2× the requested final k).
2. Builds a numbered passages prompt and asks Gemini for a JSON array of
   `{n, score}` pairs (single API call, listwise scoring).
3. Returns chunks sorted by descending rerank score; the RAG service then
   keeps the top-k for prompt construction.

The interface is a `Reranker` Protocol so a cross-encoder reranker
(e.g. `bge-reranker-base`) could be added later without changing the RAG
service. The reranker is opt-in via constructor argument; the eval runner
exposes it as `--rerank`, which is how we compare baseline vs improved.

### 5.5 Eval results on the example dataset

We ran the harness against `eval/datasets/example.json` (3 docs, 6 questions,
hand-labelled). All numbers were produced with `gemini-2.5-flash-lite` at
~$0.10/1M input tokens, ~$0.40/1M output tokens.

| Configuration       | recall@1 | recall@3 | MRR   | Faithfulness | p50 latency | p95 latency | Cost / query |
|---------------------|----------|----------|-------|--------------|-------------|-------------|--------------|
| Baseline            | 100%     | 100%     | 1.000 | —            | 3.7 s       | 4.1 s       | $0.000014    |
| Baseline + judge    | 100%     | 100%     | 1.000 | 1.000        | 3.1 s       | 3.6 s       | $0.000015    |
| Reranked            | 100%     | 100%     | 1.000 | —            | 4.4 s       | 5.5 s       | $0.000014    |
| Reranked + judge    | 100%     | 100%     | 1.000 | 1.000        | 5.5 s       | 6.2 s       | $0.000014    |

**Honest findings:**

1. **Baseline retrieval is already perfect** on this dataset. The three
   documents (France, Japan, photosynthesis) are topically distinct enough
   that embedding similarity unambiguously picks the right chunk for every
   question.
2. **Reranking adds 18–78% latency with no quality lift.** Each rerank pass
   is one extra Gemini call. For this corpus it's pure overhead — the
   measurement is exactly what the harness was built to catch. We default
   reranking to *off* and only enable it on corpora where the harness
   detects measurable recall@k lift.
3. **Faithfulness is 1.000.** The LLM-as-judge scored every answer as fully
   supported by its retrieved context — i.e., no hallucinations. The cited
   chunks always justified the answer text.
4. **Cost is negligible.** All four runs combined ran for under a tenth of
   a cent. The dominant operational cost in production would be embedding
   index updates, not per-query inference.

These findings are the strongest single argument that Lexicon is an
ML-engineering project rather than a thin LLM wrapper: every architectural
choice (baseline retrieval, reranker, chunk size, top-k) is measurable, and
we measured.

## 6. Testing strategy

Lexicon's test pyramid:

```
            ┌─────────────────┐
            │   E2E manual    │   sprint demo recordings
            ├─────────────────┤
            │  Integration    │   pytest hits Flask test_client; UI hits
            │  (API + UI)     │   the rendered DOM via @testing-library
            ├─────────────────┤
            │   Unit          │   parser, chunker, embeddings adapter,
            │                 │   vector store wrapper
            └─────────────────┘
```

### 6.1 Backend tests (Sprint 1)
Run with `cd backend && pytest`.

| File                              | Type        | What it covers                                               |
|-----------------------------------|-------------|--------------------------------------------------------------|
| `tests/test_health.py`            | integration | `/` returns service info; `/healthz` returns 200             |
| `tests/test_parser.py`            | unit        | TXT and MD parsing, latin-1 fallback, unsupported types      |
| `tests/test_documents_route.py`   | integration | Successful upload, missing file, unsupported file type, indexing call |
| `tests/test_chunker.py`           | unit        | Empty input, single-chunk pass-through, multi-chunk splits, overlap, paragraph preference |
| `tests/test_rag.py`               | unit        | Indexing path, empty corpus handling, prompt construction, citation filtering, empty question |
| `tests/test_chat_route.py`        | integration | Successful answer, validation of `question` and `top_k`      |

CI runs lint (`ruff`) and tests (`pytest --cov`) on every PR.

### 6.2 Frontend tests (Sprint 1)
Run with `cd frontend && npm test`.

| File                                            | What it covers                                       |
|-------------------------------------------------|-------------------------------------------------------|
| `src/components/__tests__/DocumentList.test.jsx`| Empty state, list rendering, character formatting    |
| `src/components/__tests__/AnswerText.test.jsx`  | Plain text rendering, single + multi-citation parsing |

CI runs lint (`eslint`), tests (`vitest`), and a production build on every PR.

### 6.3 RAG eval harness (Sprint 3, complete)
Lives in `backend/eval/`. Run with `python -m eval.runner --dataset ... --out ...`.
See `backend/eval/README.md` for the dataset format and CLI flags.

| File                              | What it covers                                                |
|-----------------------------------|---------------------------------------------------------------|
| `tests/test_eval_dataset.py`      | Dataset loading + validation (4 tests)                        |
| `tests/test_eval_metrics.py`      | recall@k, MRR, answer-match, faithfulness, latency, cost (10) |
| `tests/test_eval_judge.py`        | LLM-as-judge JSON parsing, code-fence handling, clamping (5)  |
| `tests/test_reranker.py`          | Reranker scoring + sorting + parse robustness (6)             |
| `tests/test_rag_with_reranker.py` | RAG composes reranker with overfetch (2)                      |

The harness is what turns Lexicon from "an LLM wrapper" into an
ML-engineering project. Its outputs (`eval/reports/*.json`) are the central
artifact to show in the demo and to defend design choices.

## 7. Security notes

- API keys live in `.env` only; `.env` is gitignored. CI uses a dummy key
  for tests via `GEMINI_API_KEY=dummy-for-tests`.
- CORS is restricted to the configured origins (`CORS_ORIGINS` env var).
- Upload size is capped via Flask's `MAX_CONTENT_LENGTH`.
- Uploaded text is passed through `pypdf` / `bytes.decode` only — no
  templating or shell — so injection surface is minimal.

## 8. Deployment

Backend and frontend are deployed to Render via `render.yaml` (a Render
Blueprint). The blueprint provisions both services and a 1 GB persistent
disk for Chroma at `/var/data/chroma`. Secrets (`GEMINI_API_KEY`,
`CORS_ORIGINS`, `VITE_API_BASE_URL`) are set per-service in the Render
dashboard rather than committed.

Liveness is checked via `GET /healthz`. A future `/readyz` will also
verify Gemini and Chroma connectivity.

## 9. Open questions / future work

- **Auth:** currently single-tenant, no auth. Adding Auth0 or Clerk would
  let multiple users keep separate corpora.
- **Streaming:** chat responses should stream token-by-token in Sprint 2 for
  better UX.
- **Chunk strategy ablation:** Sprint 3 will A/B fixed-size vs. recursive
  vs. semantic chunking using the eval harness.
- **Reranking:** a cross-encoder reranker (e.g. `bge-reranker-base`) on top
  of the embedding retrieval is a likely Sprint 3 improvement if recall@k
  metrics warrant it.
