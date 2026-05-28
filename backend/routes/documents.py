"""Document upload + indexing endpoints.

Sprint 1 scope: parse and return metadata.
Sprint 2 scope: also chunk, embed, and index into the vector store so the
document is queryable by /api/chat.

Indexing happens inline on upload — fine for capstone-scale corpora and
honest about latency; a future improvement (noted in DESIGN.md) is async
indexing via a job queue.
"""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from flask import Blueprint, jsonify, request

from services.parser import (
    UnsupportedFileTypeError,
    parse_document,
    supported_extensions,
)
from services.rag import get_rag_service

logger = logging.getLogger(__name__)
documents_bp = Blueprint("documents", __name__)


@documents_bp.post("/documents")
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "missing_file", "message": "No file part in request."}), 400

    upload = request.files["file"]
    if not upload.filename:
        return jsonify({"error": "missing_filename"}), 400

    try:
        text = parse_document(upload.filename, upload.stream)
    except UnsupportedFileTypeError as exc:
        return (
            jsonify(
                {
                    "error": "unsupported_file_type",
                    "message": str(exc),
                    "supported": sorted(supported_extensions()),
                }
            ),
            400,
        )
    except Exception as exc:  # noqa: BLE001 — log and return a generic 500
        logger.exception("Failed to parse uploaded document")
        return jsonify({"error": "parse_failed", "message": str(exc)}), 500

    document_id = str(uuid.uuid4())

    # Index the document. Failures here shouldn't fail the upload — we still
    # have the parsed text and can re-index later. We surface the indexing
    # status to the client so the UI can show it.
    chunks_indexed = 0
    indexing_error: str | None = None
    try:
        rag = get_rag_service()
        chunks_indexed = rag.index_document(document_id, upload.filename, text)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to index document %s", document_id)
        indexing_error = str(exc)

    body = {
        "id": document_id,
        "filename": upload.filename,
        "char_count": len(text),
        "uploaded_at": datetime.now(UTC).isoformat(),
        "preview": text[:500],
        "chunks_indexed": chunks_indexed,
    }
    if indexing_error:
        body["indexing_error"] = indexing_error
    return jsonify(body), 201


@documents_bp.get("/documents/supported-types")
def list_supported_types():
    return jsonify({"supported": sorted(supported_extensions())})
