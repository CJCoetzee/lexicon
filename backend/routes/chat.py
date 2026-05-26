"""Chat (Q&A) endpoint."""
from __future__ import annotations

import logging
from dataclasses import asdict

from flask import Blueprint, jsonify, request

from services.rag import get_rag_service

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)


@chat_bp.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    top_k = int(payload.get("top_k") or 5)

    if not question:
        return jsonify({"error": "missing_question"}), 400
    if top_k < 1 or top_k > 20:
        return jsonify({"error": "invalid_top_k", "message": "1 <= top_k <= 20"}), 400

    try:
        result = get_rag_service().answer(question, top_k=top_k)
    except Exception as exc:  # noqa: BLE001
        logger.exception("RAG pipeline failed")
        return jsonify({"error": "generation_failed", "message": str(exc)}), 500

    return jsonify(
        {
            "answer": result.answer,
            "citations": [asdict(c) for c in result.citations],
            "latency_ms": result.latency_ms,
            "retrieved": result.retrieved,
        }
    )
