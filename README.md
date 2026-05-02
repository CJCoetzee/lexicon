# Lexicon

A retrieval-augmented Q&A system for your documents. Upload PDFs or text files, ask questions, get answers with cited sources.

Built as the MSSE Capstone project for Quantic.

---

## Live demo

- **Frontend:** _(to be added after Sprint 1 deployment)_
- **Backend API:** _(to be added after Sprint 1 deployment)_

## Project artifacts

- **GitHub repo:** _(this repo)_
- **Trello Scrum board:** _(link to be added after Sprint 1)_
- **Design and testing document:** [DESIGN.md](./DESIGN.md)
- **Final demo recording:** _(to be added after final submission)_

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

```bash
cd backend
python -m venv .venv
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

## License

MIT (see [LICENSE](./LICENSE))
