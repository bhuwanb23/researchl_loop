"""1.7 — main.py skeleton: app boots, health endpoint reports honest modes."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["llm_mode"] in ("mock", "real")
    assert body["adaption_mode"] in ("emulated", "real")


def test_openapi_docs_available():
    resp = client.get("/docs")
    assert resp.status_code == 200
