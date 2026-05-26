"""Application configuration loaded from environment variables.

We use a small dataclass instead of a heavyweight settings library so the
config surface is easy to read and easy to mock in tests.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Config:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    flask_env: str = os.getenv("FLASK_ENV", "production")
    flask_debug: bool = os.getenv("FLASK_DEBUG", "0") == "1"
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
    cors_origins: List[str] = field(
        default_factory=lambda: _split_csv(
            os.getenv("CORS_ORIGINS", "http://localhost:5173")
        )
    )
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
    generation_model: str = os.getenv("GEMINI_GENERATION_MODEL", "gemini-2.5-flash-lite")
    embedding_model: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

    @property
    def is_configured(self) -> bool:
        return bool(self.gemini_api_key)


config = Config()
