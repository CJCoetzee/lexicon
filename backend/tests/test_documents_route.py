"""Integration tests for the /api/documents endpoint."""
from __future__ import annotations

import io


def test_upload_text_file_returns_201_and_metadata(client):
    data = {
        "file": (io.BytesIO(b"Hello, world! This is a test document."), "test.txt"),
    }
    response = client.post("/api/documents", data=data, content_type="multipart/form-data")
    assert response.status_code == 201
    body = response.get_json()
    assert body["filename"] == "test.txt"
    assert body["char_count"] > 0
    assert "id" in body
    assert "uploaded_at" in body
    assert "Hello, world!" in body["preview"]


def test_upload_missing_file_returns_400(client):
    response = client.post("/api/documents", data={}, content_type="multipart/form-data")
    assert response.status_code == 400
    assert response.get_json()["error"] == "missing_file"


def test_upload_unsupported_type_returns_400(client):
    data = {
        "file": (io.BytesIO(b"<html></html>"), "page.html"),
    }
    response = client.post("/api/documents", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "unsupported_file_type"
    assert ".pdf" in body["supported"]


def test_supported_types_endpoint_lists_extensions(client):
    response = client.get("/api/documents/supported-types")
    assert response.status_code == 200
    body = response.get_json()
    assert ".pdf" in body["supported"]
    assert ".txt" in body["supported"]
