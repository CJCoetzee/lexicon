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
| Embeddings     | Gemini `text-embedding-004`  | Free tier, 768-dim, good quality. Local sentence-transformers is the eval-harness alternative. |
| LLM            | Gemini `gemini-1.5-flash`    | Free tier with 1500 req/day, fast, low cost. Provider-Protocol design lets us swap.     |
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

### 5.2 Indexing and chat (Sprint 2, planned)
The full RAG flow will be added in Sprint 2 and will be documented here as
it lands: chunk → embed → upsert → on query: embed question → top-k
retrieve → prompt with cited context → return answer with span-level
citations.

### 5.3 Evaluation (Sprint 3, planned)
The eval harness will be documented here once implemented: dataset format,
metrics (recall@k, faithfulness, answer-relevance, latency, cost), and the
reproducible runner.

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
| `tests/test_documents_route.py`   | integration | Successful upload, missing file, unsupported file type       |

CI runs lint (`ruff`) and tests (`pytest --cov`) on every PR.

### 6.2 Frontend tests (Sprint 1)
Run with `cd frontend && npm test`.

| File                                            | What it covers                                       |
|-------------------------------------------------|-------------------------------------------------------|
| `src/components/__tests__/DocumentList.test.jsx`| Empty state, list rendering, character formatting    |

CI runs lint (`eslint`), tests (`vitest`), and a production build on every PR.

### 6.3 RAG eval harness (Sprint 3, planned)
A separate `backend/eval/` module will run a fixed evaluation set against
the live system and produce a JSON report with:

- **Retrieval quality:** recall@k, MRR over a hand-labelled dataset.
- **Answer quality:** LLM-as-judge faithfulness (does the answer follow
  from the retrieved context?) and answer-relevance scores.
- **Operational:** p50/p95 latency per stage, total cost per query.

This harness is what makes Lexicon an "ML-engineering" project rather than
a thin LLM wrapper, and it's the artifact to highlight in the final demo.

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
