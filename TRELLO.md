# Trello Board — Lexicon

## Card details 

### US-1 Upload PDF/TXT/MD documents
**As a** user
**I want to** upload my documents
**So that** I can ask questions about them.

Acceptance:
- Drag-and-drop or click to upload
- Supports `.pdf`, `.txt`, `.md`
- File size capped (10 MB default)
- Shows error for unsupported types
- Returns 201 with document metadata

**Sprint 1. DONE.**

### US-2 See list of uploaded documents
**As a** user
**I want to** see my uploaded documents
**So that** I know what's been indexed.

Acceptance:
- List shows filename and character count
- Empty state when no documents
- New documents prepend to the list

**Sprint 1. DONE.**

### US-3 Ask a question and receive an answer
**As a** user
**I want to** ask natural-language questions about my uploaded documents
**So that** I can find answers without reading every page.

Acceptance:
- Chat input in the right panel
- Backend retrieves top-k relevant chunks from Chroma
- Gemini generates answer grounded in retrieved context
- Returns answer in under 8 seconds for a small corpus

**Sprint 2.**

### US-4 See citations to source passages
**As a** user
**I want to** see which passage in which document supports each answer
**So that** I can verify the system isn't hallucinating.

Acceptance:
- Inline `[1]`, `[2]` markers in the answer text
- Citations panel shows the source chunk text and filename
- Clicking a citation scrolls/highlights the relevant chunk

**Sprint 2.**

### US-5 Streaming chat responses
**As a** user
**I want** answers to stream token-by-token
**So that** I see progress immediately and the UX feels fast.

**Sprint 3.**

### US-6 Source highlighting on citation click
**As a** user
**I want to** click a citation and see the supporting passage highlighted
**So that** I can quickly verify the source.

**Sprint 3.**

### US-7 Eval harness — retrieval recall@k
**As a** developer
**I want to** measure how often the correct chunk appears in the top-k results
**So that** I can iterate on chunking and retrieval.

Acceptance:
- Hand-labelled eval set (~20 question/document pairs)
- Computes recall@1, recall@3, recall@5
- Runner outputs JSON report

**Sprint 3.**

### US-8 Eval harness — answer faithfulness (LLM-as-judge)
**As a** developer
**I want** an automated faithfulness score for each answer
**So that** I can detect hallucinations regression on changes.

**Sprint 3.**

### US-9 Eval harness — latency and cost tracking
**As a** developer
**I want** per-query latency and token-cost metrics
**So that** I can defend the operational profile in the design doc.

**Sprint 3.**

### US-10 Retrieval improvement based on eval results
**As a** developer
**I want to** A/B at least one retrieval improvement (rerank or hybrid search)
**So that** the eval numbers show real iteration, not just baseline.

**Sprint 3.**

### US-11 Full unit + integration test coverage
**As a** developer
**I want** ≥80% line coverage on `services/` and integration tests on every route
**So that** future changes don't silently break behaviour.

**Sprint 3.**

### US-12 Production deploy on Render
**As an** operator
**I want** the app deployed to a free hosting tier with persistent vector data
**So that** the demo can be performed against the live URL.

**Sprint 1.**

### US-13 CI on every PR
**As a** developer
**I want** lint + tests + build to run on every PR
**So that** main is always green.

**Sprint 1. DONE.**

### US-14 Design and testing document
**As a** grader
**I want** a written explanation of architecture decisions and testing performed
**So that** I can evaluate the project against the rubric.

**Final week.**

### US-15 Final demo recording
**As a** grader
**I want** a 15–20 minute demo of the working system with all user stories shown
**So that** I can score the presentation rubric.

**Final week.**

### US-16 Adversarial eval dataset where reranker wins
**As a** developer
**I want** an evaluation dataset where embedding-only retrieval underperforms
**So that** the eval harness can demonstrate measurable lift from the reranker.

Acceptance: dataset has ≥4 topically similar documents and ≥6 questions where the
gold chunk is *not* the first result by pure embedding similarity.

**Sprint 4.**

### US-17 Document delete and clear-all
**As a** user
**I want to** remove an uploaded document, or clear all of them
**So that** I can rebuild my corpus without restarting the server.

**Sprint 4.**

### US-18 Suggested questions on upload
**As a** user
**I want to** see three suggested questions after uploading a document
**So that** I'm not staring at a blank chat input wondering what to ask.

**Sprint 4.**

### US-19 Streaming chat responses
**As a** user
**I want** the answer to type itself out token-by-token
**So that** I see progress immediately and the UX feels responsive.

**Sprint 4.**

### US-20 Multi-turn conversation memory
**As a** user
**I want to** ask follow-up questions that reference earlier turns
**So that** I can have a natural conversation rather than one-shot Q&A.

**Sprint 4.**

### US-21 Dark mode toggle
**As a** user
**I want** a dark theme I can toggle from the header
**So that** the app is comfortable to use in low light.

**Sprint 4.**
