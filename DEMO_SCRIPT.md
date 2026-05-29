# Lexicon — Final Demo Script

Target: **17 minutes** (handbook says 15-20). Speak naturally — this is a
beat sheet, not a teleprompter.

---

## Prep (5 min before recording)

1. Warm the backend so cold-start doesn't bite:
   ```
   curl https://lexicon-backend-ma4z.onrender.com/healthz
   ```
2. Open in tabs (left to right):
   - The deployed app (https://lexicon-frontend-9f1q.onrender.com)
   - GitHub repo
   - `DESIGN.md` on GitHub
   - `eval/reports/baseline_judged.json` and `hard_baseline.json`
   - Trello board
   - GitHub Actions tab (green run)
3. Have `france.txt` ready on your desktop (content from `eval/datasets/example.json`).
4. Government-issued ID in hand.
5. Zoom set to record video + screen, audio tested.

---

## The script (~17 min)

### 0:00–1:00 — Intro + ID

Camera on you.

> "I'm CJ Coetzee — MSSE Capstone project for Quantic, called **Lexicon**.
> It's a retrieval-augmented Q&A system: upload documents, ask questions,
> get answers with cited sources. I worked solo, playing all three Scrum
> roles."

Hold government ID to camera. Pause 3 seconds.

### 1:00–6:00 — Live demo (the main course)

Switch to the deployed app.

> "Live on Render's free tier."

**Toggle dark mode** (one second of preening).

**Drop `france.txt` into the upload zone.**

> "Backend parses the file, chunks it on paragraph and sentence boundaries,
> embeds each chunk with Gemini, writes to Chroma. Two chunks indexed."

> "And — three suggested starter questions appear as chips. That's a second
> Gemini call asking the model to propose questions about what I just
> uploaded. Solves the 'blank input' problem."

**Click a suggested-question chip.** The answer streams in.

> "Streaming via Server-Sent Events — tokens appear as the model generates
> them. The `[1]` is a citation."

**Click the `[1]` marker.**

> "Opens the citation panel and highlights the source. Every claim is
> anchored to a passage I uploaded."

**Type a follow-up: "what about its language?"**

> "Notice I said 'its' — no country named. The frontend sends the last six
> turns with each request, so follow-ups resolve."

**Ask an out-of-scope question** ("What is the capital of Japan?"):

> "Refuses rather than guessing. The prompt is strict about using only the
> provided context."

**Click the × on the document, then "Clear all".**

> "Document management — single delete and bulk clear, scoped to chunks in
> Chroma."

### 6:00–9:00 — Architecture (the design doc tour)

Switch to `DESIGN.md` Section 3.

> "Stack is Flask + React + Chroma + Gemini. Four patterns worth calling
> out: application factory for testable Flask instances, Strategy registry
> for file parsing — adding `.docx` is one line — Provider Protocols for
> embeddings, generation, and reranking so swapping providers doesn't
> change call sites, and a Facade around Chroma that exposes four methods
> so it's mockable in tests."

Scroll briefly to Section 4 (tech choices) and Section 8 (deployment).

> "Cost analysis here — entire eval ran for under a cent. Deployment trade
> off documented: free tier uses ephemeral storage, paid upgrade swaps in a
> persistent disk with no code changes."

### 9:00–12:00 — Eval framework (the ML-engineering differentiator)

Switch to `baseline_judged.json`.

> "This is what turns the project from 'I called an LLM API' into ML
> engineering. The eval harness in `backend/eval/` runs a labelled dataset
> through the full pipeline and outputs six metrics: recall@k, MRR,
> answer-substring match, LLM-as-judge faithfulness, latency, cost."

Open `hard_baseline.json` next to it.

> "Two datasets. Easy: three unrelated docs, six questions. Hard: five
> topically-similar European countries, eight questions designed to trip
> embedding retrieval."

> "Headline numbers: **100% recall@1 on both datasets, 1.000 faithfulness,
> no hallucinations**. I built a Gemini-as-reranker for Sprint 3 and ran
> it against both datasets — it added 18 to 78% latency with zero quality
> lift on these corpora."

> "The honest engineering finding is: **reranking is overhead on
> well-separated content**. Default off. The framework makes that a
> data-driven decision rather than dogma. If we move to a corpus where
> retrieval misses, the harness detects it and reranking earns its keep."

### 12:00–14:30 — Engineering practices

Switch to GitHub Actions (green run).

> "CI runs on every PR — ruff lint, pytest with coverage, eslint, vitest,
> production build. 57 backend tests, 8 frontend tests, all green."

Switch to Trello.

> "Twenty-one user stories across four sprints. Handbook calls for at
> least three. Sprint 1 was foundations, Sprint 2 was core RAG, Sprint 3
> was the eval framework and reranker. Sprint 4 was an optional polish
> sprint — streaming, multi-turn memory, suggested questions, dark mode,
> document delete, the adversarial eval dataset."

Switch briefly to the test directory in the IDE.

> "Testing uses fakes that don't touch Gemini or Chroma, so the suite runs
> offline in under two seconds."

### 14:30–16:00 — Reflection

> "Three things I'd do differently with more time. Async indexing so
> uploads don't block on embed-and-store. A larger adversarial eval set
> where the reranker actually earns its keep — the current Gemini
> embedding model was good enough that even my hard dataset didn't break
> baseline. And a chunk-strategy ablation using the same harness."

> "What I'd carry forward is the discipline of measuring before improving.
> Every architectural choice in this repo has a number attached to it.
> That's the muscle I wanted to develop and I think it shows."

### 16:00–17:00 — Wrap

> "Recap of deliverables: GitHub repo shared with quantic-grader,
> deployed app on Render at the URL in the README, Trello board with 21
> stories across four sprints, design and testing document, and four eval
> reports comparing baseline against reranked on both an easy and a hard
> dataset."

> "Thanks for grading — I'm CJ Coetzee, that was Lexicon."

Stop recording.

---

## Submit (after recording)

1. Watch the recording once. Check: ID visible early, audio clear, 15-20 min length.
2. Upload to YouTube as **Unlisted**.
3. Submit on Quantic dashboard:
   - GitHub: https://github.com/CJCoetzee/lexicon
   - App: https://lexicon-frontend-9f1q.onrender.com
   - Trello: https://trello.com/b/69f63c86cb80f47ed2c384bd/lexicon
   - DESIGN.md: https://github.com/CJCoetzee/lexicon/blob/main/DESIGN.md
   - Demo video (YouTube unlisted link)

---

## Don't forget

- Warm the backend with `/healthz` 30 seconds before recording.
- Speak up, project to the back of the room.
- Don't read the script word-for-word — hit the beats in your own words.
- 21 minutes is fine. 25+ drops you a rubric tier.
- ID must appear on camera early.
