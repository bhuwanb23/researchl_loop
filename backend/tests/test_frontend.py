"""Phase 4 — frontend serving tests (static SPA served by FastAPI).

The SPA is vanilla HTML/CSS/JS (no build step), organized as:
    frontend/index.html
    frontend/css/{tokens,base,components}.css
    frontend/js/{main,api,ui,stepper}.js + frontend/js/views/*.js
These tests verify the backend serves it correctly and the API still
responds alongside it.
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
    # new organized structure referenced from index.html
    assert "css/tokens.css" in body
    assert "css/base.css" in body
    assert "css/components.css" in body
    assert "js/main.js" in body


def test_static_assets_served():
    for css in ("/css/tokens.css", "/css/base.css", "/css/components.css"):
        resp = client.get(css)
        assert resp.status_code == 200
        assert "text/css" in resp.headers["content-type"]
    assert "--accent" in client.get("/css/tokens.css").text  # design tokens present

    for js in ("/js/main.js", "/js/api.js", "/js/ui.js", "/js/stepper.js", "/js/views/audit.js"):
        resp = client.get(js)
        assert resp.status_code == 200
        assert "javascript" in resp.headers["content-type"]

    # API contract strings live in the api module + views
    api_js = client.get("/js/api.js").text
    for path in ("/api/scope", "/api/receipts", "/api/exports", "/api/datasets/invent", "/api/datasets/augment", "/api/health"):
        assert path in api_js


def test_api_routes_survive_static_mount():
    """The static mount at "/" must not shadow API routes."""
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    scope = client.post("/api/scope", json={"question": "Does study time affect exam scores?", "session_id": "s"})
    assert scope.status_code == 200
    assert scope.json()["dataset_name"] == "study_vs_scores"


def test_sample_csv_route():
    resp = client.get("/api/samples/messy_study_survey.csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "weekly_hours" in resp.text
