"""Document upload + indexing endpoints.

Sprint 1: parse and return metadata.
Sprint 2: also chunk, embed, and index for retrieval.
Sprint 4: add LLM-generated suggested questions on upload, plus delete /
clear endpoints.
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
from services.suggestions import generate_suggested_questions

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
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to parse uploaded document")
        return jsonify({"error": "parse_failed", "message": str(exc)}), 500

    document_id = str(uuid.uuid4())

    # Index. Failures here don't fail the upload -- we still parsed the text.
    chunks_indexed = 0
    indexing_error: str | None = None
    try:
        rag = get_rag_service()
        chunks_indexed = rag.index_document(document_id, upload.filename, text)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to index document %s", document_id)
        indexing_error = str(exc)

    # Best-effort suggested questions. Empty list on failure.
    suggested = generate_suggested_questions(text)

    body = {
        "id": document_id,
        "filename": upload.filename,
        "char_count": len(text),
        "uploaded_at": datetime.now(UTC).isoformat(),
        "preview": text[:500],
        "chunks_indexed": chunks_indexed,
        "suggested_questions": suggested,
    }
    if indexing_error:
        body["indexing_error"] = indexing_error
    return jsonify(body), 201


@documents_bp.get("/documents/supported-types")
def list_supported_types():
    return jsonify({"supported": sorted(supported_extensions())})


@documents_bp.get("/documents")
def list_documents():
    """Return the documents currently indexed in the vector store.

    Used by the frontend to rehydrate its document list on page mount so
    refreshes don't lose the user's session.
    """
    try:
        from services.vector_store import get_vector_store
        docs = get_vector_store().list_documents()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to list documents")
        return jsonify({"error": "list_failed", "message": str(exc)}), 500
    return jsonify({"documents": docs}), 200


@documents_bp.delete("/documents/<document_id>")
def delete_document(document_id: str):
    try:
        from services.vector_store import get_vector_store
        deleted = get_vector_store().delete_document(document_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to delete document %s", document_id)
        return jsonify({"error": "delete_failed", "message": str(exc)}), 500
    return jsonify({"id": document_id, "chunks_removed": deleted}), 200


@documents_bp.delete("/documents")
def clear_all_documents():
    try:
        from services.vector_store import get_vector_store
        store = get_vector_store()
        before = store.count()
        store.reset()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to clear documents")
        return jsonify({"error": "clear_failed", "message": str(exc)}), 500
    return jsonify({"chunks_removed": before}), 200
