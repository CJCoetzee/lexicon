"""Health check endpoints used by Render and uptime monitoring."""
from __future__ import annotations

from flask import Blueprint, jsonify

from config import config

health_bp = Blueprint("health", __name__)


@health_bp.get("/")
def root():
    return jsonify(
        {
            "service": "lexicon",
            "status": "ok",
            "configured": config.is_configured,
        }
    )


@health_bp.get("/healthz")
def healthz():
    """Liveness probe — returns 200 if the process is up.

    A separate /readyz could check Chroma + Gemini connectivity once those
    are wired in. For Sprint 1 we keep it simple.
    """
    return jsonify({"status": "ok"}), 200
