"""Health endpoint tests."""
from __future__ import annotations


def test_root_returns_service_info(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["service"] == "lexicon"
    assert data["status"] == "ok"
    assert "configured" in data


def test_healthz_returns_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
