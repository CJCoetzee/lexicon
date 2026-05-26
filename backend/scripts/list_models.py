"""List Gemini models available to your API key.

Useful when Google deprecates a model and our defaults stop working. Run:

    python scripts/list_models.py

(from the backend/ directory, with the venv activated and .env populated.)

We hit the REST endpoint directly because the SDK's `client.models.list()`
returns 501 UNIMPLEMENTED on some projects.
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests

# Allow `python scripts/list_models.py` from the backend/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import config  # noqa: E402


LIST_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def main() -> int:
    if not config.gemini_api_key:
        print("GEMINI_API_KEY is not set. Populate backend/.env first.")
        return 1

    response = requests.get(LIST_URL, params={"key": config.gemini_api_key}, timeout=30)
    if not response.ok:
        print(f"HTTP {response.status_code}: {response.text}")
        return 1

    data = response.json()
    models = data.get("models", [])

    generation: list[tuple[str, str]] = []
    embedding: list[tuple[str, str]] = []
    other: list[tuple[str, list[str]]] = []

    for m in models:
        name = m.get("name", "").removeprefix("models/")
        methods = m.get("supportedGenerationMethods", []) or []
        display = m.get("displayName", "")
        if "generateContent" in methods:
            generation.append((name, display))
        elif "embedContent" in methods or "batchEmbedContents" in methods:
            embedding.append((name, display))
        else:
            other.append((name, methods))

    def _print(title: str, rows: list) -> None:
        print(title)
        # We can't sort+set across mixed shapes; dedupe by name only.
        seen: set[str] = set()
        keyed = []
        for row in rows:
            name = row[0]
            if name in seen:
                continue
            seen.add(name)
            keyed.append(row)
        for row in sorted(keyed, key=lambda r: r[0]):
            name, extra = row[0], row[1]
            print(f"  {name:<40s}  {extra}")
        print()

    print(f"\nListing {len(models)} models accessible to your API key:\n")
    _print("Generation models (use for GEMINI_GENERATION_MODEL):", generation)
    _print("Embedding models (use for GEMINI_EMBEDDING_MODEL):", embedding)
    if other:
        _print("Other:", other)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
