"""Phase 4 — frontend serving tests (static SPA served by FastAPI).

The SPA is vanilla HTML/CSS/JS (no build step); these tests verify the
backend serves it correctly and the API still responds alongside it.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_index_served():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    body = resp.text
    assert "ResearchLoop" in body
    # 5 screens + nav present
    for screen in ("screen-ask", "screen-build", "screen-audit", "screen-receipt", "screen-export"):
        assert screen in body


def test_static_assets_served():
    css = client.get("/styles.css")
    assert css.status_code == 200
    assert "text/css" in css.headers["content-type"]
    assert "--indigo" in css.text  # design tokens present

    js = client.get("/app.js")
    assert js.status_code == 200
    assert "javascript" in js.headers["content-type"]
    assert "/api/scope" in js.text
    assert "/api/receipts" in js.text
    assert "/api/exports" in js.text


def test_api_routes_survive_static_mount():
    """The static mount at "/" must not shadow API routes."""
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    scope = client.post("/api/scope", json={"question": "Does study time affect exam scores?", "session_id": "s"})
    assert scope.status_code == 200
    assert scope.json()["dataset_name"] == "study_vs_scores"
