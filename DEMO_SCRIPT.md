# Lexicon — Final Demo Script

Target length: **15–20 minutes**. Hit the rubric items: clear functionality
demo, professional delivery, you visible + audible, government ID shown.

---

## Before you hit record (5-minute prep)

1. **Warm up the backend** so cold start doesn't bite you on camera:
   ```
   curl https://lexicon-backend-ma4z.onrender.com/healthz
   curl https://lexicon-backend-ma4z.onrender.com/
   ```
   Wait until both return 200 with quick latency.

2. **Open these tabs in order** so you can switch with one click during the demo:
   - https://lexicon-frontend-9f1q.onrender.com (the live app)
   - https://github.com/CJCoetzee/lexicon (repo)
   - https://github.com/CJCoetzee/lexicon/blob/main/DESIGN.md (design doc)
   - https://github.com/CJCoetzee/lexicon/blob/main/backend/eval/reports/baseline_judged.json (eval report)
   - https://github.com/CJCoetzee/lexicon/blob/main/backend/eval/reports/reranked_judged.json (eval report)
   - https://trello.com/b/69f63c86cb80f47ed2c384bd/lexicon (Trello board)
   - Your IDE open on the repo (for the code walkthrough)
   - The CI tab on GitHub Actions showing a green run

3. **Have a sample document ready** — make a small `france.txt` on your desktop with the same content as `eval/datasets/example.json`'s France document. You'll upload it during the demo.

4. **Government-issued ID** in your hand. Driver's license or passport, photo and name clearly visible. You'll hold it to the camera in the intro.

5. **Recording tool** — Zoom is what the handbook recommends. Set it to record video (you) + screen share. Test audio levels with a 10-second test clip before going live.

---

## The script

Aim for the timings below but don't be rigid. The rubric flags "significantly outside the time requirement" — 14 or 21 minutes is fine, 25+ is not.

### 0:00–1:30 — Intro + ID (~90s)

> "Hi, I'm CJ Coetzee. This is my MSSE Capstone project for Quantic, called **Lexicon**. Lexicon is a retrieval-augmented question-answering system: you upload documents and ask natural-language questions, and the system returns answers with inline citations to the source passages it used."

Hold your government-issued ID up to the camera. Pause for 3 seconds so the name and photo are legible to the grader.

> "Before I dive in, I want to flag this is a solo project — I worked individually rather than as a team. I played all three Scrum roles: Product Owner, Scrum Master, and developer."

### 1:30–3:00 — Problem statement and project framing (~90s)

> "The problem Lexicon solves: searching long documents returns pages, not answers, and rarely tells you which passage justifies a claim. For researchers, students, or analysts dealing with technical PDFs, that costs time and erodes trust in the result."

> "My approach was to build a small RAG — retrieval-augmented generation — system: a vector index over chunked document text, an LLM that grounds its answer in retrieved chunks, and inline citations the user can click to verify."

> "The 'ML-engineering' angle of this project — and what I think distinguishes it from just calling an API — is an honest evaluation framework: a way to measure retrieval quality, answer faithfulness, latency, and cost on a labelled dataset, and iterate based on what the numbers show. I'll demo that toward the end."

### 3:00–7:30 — Live app demo (~4.5 min)

Switch to the deployed app.

> "Here's the deployed version on Render's free tier. I'll upload a document, then ask a few questions."

**Action: Toggle dark mode** (header sun/moon icon):

> "Quick aesthetic note — the app supports dark mode, persisted in localStorage. I'll leave it on dark for the rest of the demo."

**Action: Drag `france.txt` into the upload zone.** Talk through what's happening:

> "When I upload, the backend parses the text — PDF, plain text, or markdown — chunks it with a recursive character splitter that respects paragraph and sentence boundaries, embeds each chunk with Gemini's embedding model, and writes them into a Chroma vector index. Two chunks indexed."

> "The app then makes a second LLM call asking Gemini to suggest three starter questions about the document I just uploaded — they appear as chips above the chat input. Solves the 'what do I ask' cold-start problem for new users."

**Action: Click one of the suggested-question chips.** The answer **streams token-by-token**:

> "Notice the answer streams in real time — tokens appear as the model generates them, rather than blocking until completion. This uses Server-Sent Events from the Flask backend, consumed by a fetch ReadableStream in React."

> "The answer cites source [1]. If I click the citation marker..." [click] "...the source panel opens, scrolls to that chunk, and briefly highlights it. So I can verify the model isn't hallucinating — every claim is anchored to a passage I uploaded."

**Action: Ask a follow-up like "what about its language?"** to show multi-turn memory:

> "Notice I just said 'its language' without naming the country. The frontend sends the last six conversation turns with every request, so follow-up questions resolve correctly against prior context."

**Action: Ask a deliberately out-of-scope question** like "What is the capital of Japan?" (with only France uploaded):

> "Notice the system refuses rather than guessing — the prompt instructs the model to only use the provided context. This is a faithfulness property the eval framework verifies, which I'll get to."

**Action: Click the × on the France document, then "Clear all":**

> "Document management — single delete and bulk clear, both wired to DELETE endpoints that scope to the document's chunks in Chroma."

### 7:30–11:00 — Architecture walkthrough (~3.5 min)

Switch to the design doc on GitHub.

> "Quick architecture tour. The stack is Python/Flask backend, React/Vite/Tailwind frontend, Chroma for the vector index, and Gemini for both embeddings and generation. The full rationale for each choice is in the design doc."

Scroll to Section 3 — Architectural patterns:

> "Four patterns worth calling out. **Application factory** for Flask so I can spin up isolated app instances per test. **Strategy pattern** for the document parser — file extensions map to extractor functions in a registry, so adding `.docx` is a one-line change. **Provider Protocols** for the embedding and generation services — Gemini today, but the interface lets me swap to Anthropic, Groq, or local sentence-transformers without changing call sites. And a **Facade** wrapping Chroma so the rest of the code only sees four methods, which made it trivial to swap implementations for tests."

Scroll to Section 4 — Technology choices, briefly:

> "Cost analysis is in here too. Total cost for the eval runs I'm about to show was under a tenth of a cent. For a production deployment I recommend Render Starter at $14 a month over self-hosting — the operational burden of patching and securing a VPS dwarfs the cost difference at this scale."

Switch to the IDE briefly to show the repo layout:

> "Code is organized into `routes/`, `services/`, `tests/`, and `eval/`. Each service is single-purpose and dependency-injected; tests use fakes so the entire suite runs offline in under two seconds."

### 11:00–14:30 — Eval framework — the differentiator (~3.5 min)

Switch to the `baseline_judged.json` report on GitHub.

> "This is where the project moves from 'I called an LLM API' to ML engineering. The eval harness lives in `backend/eval/`. It takes a JSON dataset of documents + labelled questions, indexes them into an isolated Chroma collection, runs every question through the full RAG pipeline, and produces a JSON report with six metrics: retrieval recall@k, mean reciprocal rank, answer-substring match, LLM-as-judge faithfulness, latency percentiles, and estimated USD cost."

Open both the baseline and reranked report side by side. Highlight the metrics section.

> "Comparing baseline against my reranker — a Gemini-as-reranker that takes the top-k chunks, asks Gemini to score each for relevance, and re-sorts — on this 6-question example dataset, baseline recall@1 is 100%. The reranker also hits 100%. But the reranker is 18 to 78 percent slower because it adds an extra LLM call per query."

> "This is exactly the failure mode the eval framework was built to catch. The honest engineering finding is: **on this small, topically-distinct corpus, reranking is pure overhead**. I don't enable it by default. The design document records this as a deliberate decision backed by numbers, not a default-on cargo cult."

> "In Sprint 4 I added a second dataset — `hard.json` — with five topically-similar documents (European countries) and eight questions phrased to share keywords with non-gold docs. This is where reranking should actually earn its keep. The harness measures both corpora identically and lets me decide per-deployment whether reranking is justified by the quality lift."

> "Faithfulness scored 1.000 across all runs — every answer the LLM produced was fully supported by the cited context. No hallucinations on this dataset."

### 14:30–17:00 — Engineering practices (~2.5 min)

Switch to the GitHub Actions tab showing a green CI run:

> "Every pull request runs CI — ruff lint and pytest on backend, eslint and vitest on frontend, plus a production frontend build. 57 backend tests, 8 frontend tests, all green."

Switch to the Trello board:

> "The Trello board has user stories US-1 through US-21 across four sprints. Sprint 1 was the foundation — repo, CI, deployed shell, upload. Sprint 2 was core RAG: chunking, retrieval, generation, chat UI. Sprint 3 was the eval framework, the reranker, UI polish, and deployment hardening. The handbook calls for at least three sprints, but I added an optional Sprint 4 for polish: streaming responses, multi-turn memory, suggested questions, dark mode, document delete, and the adversarial eval dataset. Every story moved through Backlog → Sprint Backlog → In Progress → Review → Done as I worked."

Switch back to the design doc Section 6 — Testing:

> "Testing pyramid: unit tests on the chunker, parser, embeddings adapter, RAG orchestrator, eval metrics, and reranker. Integration tests using Flask's test client for every API route. The unit tests use fakes that never touch Gemini or Chroma, which keeps CI fast and offline."

### 17:00–19:00 — Reflection (~2 min)

> "Three things I'd do differently with more time. First, async indexing — right now uploads block until embedding finishes. A job queue with a background worker would lift user-perceived latency. Second, a bigger and more adversarial eval dataset — six questions on three distinct documents is too easy for baseline retrieval to fail, which is why my reranker showed no lift. With a harder corpus the harness would actually justify itself. Third, a chunk-strategy ablation — fixed-size versus recursive versus semantic chunking — using the same harness."

> "What I'd carry forward is the discipline of measuring before improving. Every architectural choice in this project has a number attached to it in the design doc — chunk size, top-k, model, reranker on or off. That's the muscle I most wanted to develop in this capstone, and I think it shows in the result."

### 19:00–20:00 — Wrap-up (~1 min)

> "To recap the deliverables: a GitHub repository with documented code shared with quantic-grader; a live deployment on Render at the URL in the README; a Trello board with all user stories tracked through three sprints; a detailed design and testing document covering architecture decisions, patterns, deployment trade-offs, and the full test inventory; and four eval reports demonstrating both retrieval quality and the honest finding that reranking didn't lift quality on this corpus."

> "Thanks for grading — I'm CJ Coetzee, and that was Lexicon."

Stop recording.

---

## Submission checklist (after recording)

1. **Watch your recording all the way through** before submitting. Sanity-check audio, screen visibility, ID visible early, length 15–20 min.
2. **Upload to YouTube as Unlisted** (or Google Drive / OneDrive / Dropbox — *not* WeTransfer, the handbook flagged that link type).
3. **Submit on Quantic dashboard** with these five links:
   - GitHub repo: https://github.com/CJCoetzee/lexicon
   - Deployed app: https://lexicon-frontend-9f1q.onrender.com
   - Trello board: https://trello.com/b/69f63c86cb80f47ed2c384bd/lexicon
   - Design doc: https://github.com/CJCoetzee/lexicon/blob/main/DESIGN.md
   - Demo video: _(your unlisted YouTube link)_

Don't tell anyone the video is unlisted — that's deliberate, it just means it's not in YouTube search.

---

## Common demo pitfalls to avoid

- **Cold-start delay** — always warm the backend before recording. If you hit a 30s spinner mid-demo, the grader sees a stalled UI.
- **Reading the script word-for-word** — the script is a structure, not a teleprompter. Hit the bullets in your own words and don't worry if you skip a sentence.
- **Going long** — 21 minutes is OK. 25 minutes is "significantly outside time requirement" and drops you a rubric tier.
- **Forgetting to show the ID early** — graders flag presentations where the ID never appears.
- **Whispering** — speak up, project to the back of the room. Audio clarity matters more than video.
