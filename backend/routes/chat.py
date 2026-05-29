"""Chat (Q&A) endpoints -- non-streaming and streaming."""
from __future__ import annotations

import json
import logging
from dataclasses import asdict

from flask import Blueprint, Response, jsonify, request

from services.rag import get_rag_service

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)


def _parse_top_k(payload: dict):
    """Returns (top_k, None) or (None, (error_code, http_status))."""
    raw = payload.get("top_k")
    try:
        top_k = int(raw) if raw is not None else 5
    except (TypeError, ValueError):
        return None, ("invalid_top_k", 400)
    if top_k < 1 or top_k > 20:
        return None, ("invalid_top_k", 400)
    return top_k, None


@chat_bp.post("/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    history = payload.get("history") or []
    top_k, err = _parse_top_k(payload)

    if not question:
        return jsonify({"error": "missing_question"}), 400
    if err:
        return jsonify({"error": err[0], "message": "1 <= top_k <= 20"}), err[1]

    try:
        result = get_rag_service().answer(question, top_k=top_k, history=history)
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


@chat_bp.post("/chat/stream")
def chat_stream():
    """Server-Sent Events streaming endpoint.

    Each event is `data: {...}\n\n` with a JSON payload whose `type` field
    is one of: token, done, error.
    """
    payload = request.get_json(silent=True) or {}
    question = (payload.get("question") or "").strip()
    history = payload.get("history") or []
    top_k, err = _parse_top_k(payload)

    if not question:
        return jsonify({"error": "missing_question"}), 400
    if err:
        return jsonify({"error": err[0], "message": "1 <= top_k <= 20"}), err[1]

    rag = get_rag_service()

    def stream():
        try:
            for event in rag.answer_stream(question, top_k=top_k, history=history):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:  # noqa: BLE001
            logger.exception("Streaming RAG failed")
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return Response(
        stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
