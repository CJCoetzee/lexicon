"""Integration tests for the /api/chat endpoint."""
from __future__ import annotations


def test_chat_returns_answer_and_citations(client):
    response = client.post("/api/chat", json={"question": "What is X?"})
    assert response.status_code == 200
    body = response.get_json()
    assert "answer" in body
    assert "citations" in body
    assert isinstance(body["citations"], list)
    assert "latency_ms" in body
    assert "retrieved" in body


def test_chat_rejects_missing_question(client):
    response = client.post("/api/chat", json={})
    assert response.status_code == 400
    assert response.get_json()["error"] == "missing_question"


def test_chat_rejects_empty_question(client):
    response = client.post("/api/chat", json={"question": "   "})
    assert response.status_code == 400


def test_chat_rejects_invalid_top_k(client):
    response = client.post("/api/chat", json={"question": "ok?", "top_k": 0})
    assert response.status_code == 400
    response = client.post("/api/chat", json={"question": "ok?", "top_k": 50})
    assert response.status_code == 400


def test_chat_accepts_valid_top_k(client):
    response = client.post("/api/chat", json={"question": "ok?", "top_k": 3})
    assert response.status_code == 200
