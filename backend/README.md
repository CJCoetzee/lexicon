# Lexicon backend

Flask API for the Lexicon RAG system.

## Setup

Requires Python 3.11 or 3.12 (not 3.13 — pinned NumPy has no 3.13 wheel yet).

```bash
py -3.12 -m venv .venv       # Windows
python3.12 -m venv .venv     # macOS/Linux
source .venv/bin/activate    # macOS/Linux
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
cp .env.example .env         # then edit and add GEMINI_API_KEY
python app.py
```
Backend runs on http://localhost:5000.

## Endpoints (Sprint 1)

| Method | Path                              | Purpose                                |
|--------|-----------------------------------|----------------------------------------|
| GET    | `/`                               | Service status                          |
| GET    | `/healthz`                        | Liveness probe                          |
| POST   | `/api/documents`                  | Upload PDF/TXT/MD, get parsed text back |
| GET    | `/api/documents/supported-types`  | List supported file extensions          |

## Tests

```bash
pytest                # run all tests
pytest --cov          # with coverage
ruff check .          # lint
```

## Deployment

Production is launched via gunicorn:

```bash
gunicorn --bind 0.0.0.0:$PORT 'app:create_app()'
```
