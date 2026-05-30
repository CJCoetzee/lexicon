# Lexicon

A retrieval-augmented Q&A system for your documents. Upload PDFs or text files, ask questions, get answers with cited sources. Features streaming responses, multi-turn conversations, source-click citation jumping, document management, suggested starter questions, dark mode, and a measurement-driven evaluation harness.

Built as the MSSE Capstone project for Quantic. Four sprints (one above the handbook's minimum of three): foundations, core RAG, eval harness + reranker, then polish + extensions.

---

## Live demo

- **Frontend:** https://lexicon-frontend-9f1q.onrender.com
- **Backend API:** https://lexicon-backend-ma4z.onrender.com

Hosted on Render free tier — first request after 15 minutes of inactivity
takes ~30–60s to wake the backend. Subsequent requests are fast.

## Project artifacts

- **GitHub repo:** https://github.com/CJCoetzee/lexicon
- **Trello Scrum board:** https://trello.com/b/69f63c86cb80f47ed2c384bd/lexicon
- **Design and testing document:** [DESIGN.md](./DESIGN.md)

## Tech stack

| Layer        | Choice                                    |
|--------------|-------------------------------------------|
| Backend      | Python 3.11, Flask, Flask-CORS            |
| Frontend     | React 18, Vite, Tailwind CSS              |
| Vector store | Chroma (embedded, persistent)             |
| Embeddings   | Google `text-embedding-004` (free tier)   |
| Generation   | Google `gemini-1.5-flash` (free tier)     |
| PDF parsing  | pypdf                                     |
| Testing      | pytest (backend), Vitest (frontend)       |
| CI/CD        | GitHub Actions                            |
| Hosting      | Render (free tier)                        |

See [DESIGN.md](./DESIGN.md) for the rationale behind each choice.

## Repository layout

```
lexicon/
├── backend/              # Flask API
│   ├── app.py
│   ├── config.py
│   ├── routes/           # HTTP route handlers
│   ├── services/         # Business logic (parsing, embeddings, LLM, vector store)
│   ├── tests/            # pytest suite
│   ├── requirements.txt
│   └── .env.example
├── frontend/             # React + Vite app
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── .github/workflows/    # CI/CD
├── DESIGN.md             # Design and testing document
└── README.md
```

## Local development

### Backend

Requires Python **3.11 or 3.12**. Python 3.13 is not yet supported because
pinned NumPy 1.26.x has no 3.13 wheel on PyPI.

```bash
cd backend
py -3.12 -m venv .venv             # Windows; use `python3.12 -m venv .venv` on macOS/Linux
source .venv/bin/activate          # macOS/Linux
.venv\Scripts\activate             # Windows
pip install -r requirements.txt
cp .env.example .env               # then edit .env and add your GEMINI_API_KEY
python app.py
```

The backend runs on http://localhost:5000.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on http://localhost:5173.

## Running tests

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```
