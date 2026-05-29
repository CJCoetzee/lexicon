"""Generation service.

Wraps the Gemini chat model behind a Protocol so we can swap providers
without changing call sites. Includes retry-with-backoff for transient
per-minute rate limits, and a streaming variant for Sprint 4.
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

_MAX_RETRIES = 3
_MAX_BACKOFF_SECONDS = 60


class GenerationProvider(Protocol):
    def generate(self, prompt: str) -> str: ...

    def generate_stream(self, prompt: str):
        """Yield response text chunks as they arrive from the model."""
        ...


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

    def generate_stream(self, prompt: str):
        """Stream Gemini's response chunk-by-chunk."""
        stream = self._client.models.generate_content_stream(
            model=self._model,
            contents=prompt,
        )
        for chunk in stream:
            text = getattr(chunk, "text", None)
            if text:
                yield text


def _is_transient_rate_limit(exc: genai_errors.ClientError) -> bool:
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
    return 30


_singleton: GenerationProvider | None = None


def get_generation_provider() -> GenerationProvider:
    global _singleton
    if _singleton is None:
        _singleton = GeminiGenerationProvider()
    return _singleton
