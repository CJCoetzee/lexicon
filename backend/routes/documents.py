"""Document upload endpoints.

Sprint 1 scope: accept a file, parse its text, return the extracted text and
basic metadata. We do NOT yet chunk, embed, or store — that's Sprint 2.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from services.parser import (
    UnsupportedFileTypeError,
    parse_document,
    supported_extensions,
)

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
    except Exception as exc:  # noqa: BLE001 — we log and return a generic 500
        logger.exception("Failed to parse uploaded document")
        return jsonify({"error": "parse_failed", "message": str(exc)}), 500

    document_id = str(uuid.uuid4())
    return (
        jsonify(
            {
                "id": document_id,
                "filename": upload.filename,
                "char_count": len(text),
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "preview": text[:500],
            }
        ),
        201,
    )


@documents_bp.get("/documents/supported-types")
def list_supported_types():
    return jsonify({"supported": sorted(supported_extensions())})
