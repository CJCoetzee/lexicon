"""Generation service.

Wraps the Gemini chat model behind a Protocol so we can swap providers
(Anthropic, Groq, local Llama) without changing call sites. Includes a small
retry-with-backoff for transient per-minute rate limits.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Protocol

from google import genai
from google.genai import errors as genai_errors

from config import config

logger = logging.getLogger(__name__)


# Daily quota errors aren't retryable; per-minute ones recover in seconds.
# We bound total wait so a stuck retry can't hang the eval forever.
_MAX_RETRIES = 3
_MAX_BACKOFF_SECONDS = 60


class GenerationProvider(Protocol):
    def generate(self, prompt: str) -> str: ...


class GeminiGenerationProvider:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self._client = genai.Client(api_key=api_key or config.gemini_api_key)
        self._model = model or config.generation_model

    def generate(self, prompt: str) -> str:
        attempt = 0
        while True:
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                )
                return response.text or ""
            except genai_errors.ClientError as exc:
                attempt += 1
                if attempt > _MAX_RETRIES or not _is_transient_rate_limit(exc):
                    raise
                delay = min(_extract_retry_delay(exc), _MAX_BACKOFF_SECONDS)
                logger.warning(
                    "Gemini rate-limited (attempt %s/%s) -- sleeping %ss",
                    attempt, _MAX_RETRIES, delay,
                )
                time.sleep(delay)


def _is_transient_rate_limit(exc: genai_errors.ClientError) -> bool:
    """True for per-minute 429s. Daily-quota 429s aren't transient -- once
    we've hit them no amount of waiting helps inside the run window."""
    if getattr(exc, "status_code", None) != 429:
        return False
    msg = str(exc)
    if "PerDay" in msg:
        return False
    return "PerMinute" in msg or "RetryInfo" in msg or "retryDelay" in msg


def _extract_retry_delay(exc: genai_errors.ClientError) -> int:
    match = re.search(r"retry in (\d+)", str(exc), re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r'retryDelay["\']?\s*:\s*["\']?(\d+)', str(exc))
    if match:
        return int(match.group(1))
    return 30  # fallback


_singleton: GenerationProvider | None = None


def get_generation_provider() -> GenerationProvider:
    global _singleton
    if _singleton is None:
        _singleton = GeminiGenerationProvider()
    return _singleton
