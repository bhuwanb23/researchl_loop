"""2.9 / 2.10 — API integration tests.

Mock mode: 3 templates × {invent, augment} happy paths + error paths.
Real mode: same matrix, skipped gracefully when no LLM_API_KEY is configured.
"""

import base64
import io
import os

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.core import config
from app.main import app
from app.core.schemas import InventRequest, ScopeRequest

client = TestClient(app)

QUESTIONS = [
    "Does study time affect exam scores?",
    "Which local plant species tolerates heat best?",
    "Do students who study in groups score higher?",
]


def _scope(question: str) -> dict:
    resp = client.post("/api/scope", json={"question": question, "session_id": "sess-api"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["mode"] == config.llm_mode()
    return body


def _messy_csv_b64() -> str:
    df = pd.DataFrame({
        "study_mode": ["group", "solo", "group", "solo"],
        "weekly_hours": [3, 5, 8, 10],
        "quiz_score": [60, 70, 80, 90],
    })
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return base64.b64encode(buf.getvalue().encode()).decode()


# ---------------------------------------------------------------- F1

def test_scope_all_three_templates():
    for q in QUESTIONS:
        body = _scope(q)
        assert body["research_type"] in {"classification", "regression", "descriptive", "survey"}
        assert body["variables"], "variables required"
        assert body["suggested_rows"] > 0
        assert body["refinements"], "F7 refinements expected for templates"


def test_scope_free_question():
    resp = client.post("/api/scope", json={"question": "something completely new and vague"})
    assert resp.status_code == 200
    assert resp.json()["research_type"] == "descriptive"


def test_scope_empty_question_rejected():
    resp = client.post("/api/scope", json={"question": "   "})
    assert resp.status_code == 400


def test_scope_refinement_flow():
    body = _scope(QUESTIONS[0])
    refinement = body["refinements"][0]
    resp = client.post("/api/scope", json={"question": QUESTIONS[0], "refinement": refinement})
    assert resp.status_code == 200
    assert resp.json()["dataset_name"] == "study_vs_scores"


# ---------------------------------------------------------------- F2

def test_invent_all_three_templates():
    for q in QUESTIONS:
        plan = _scope(q)
        resp = client.post("/api/datasets/invent", json={
            "session_id": "sess-api",
            "plan": plan,
            "rows": 80,
        })
        assert resp.status_code == 200, resp.text
        ds = resp.json()
        assert len(ds["rows"]) == 80
        assert all(r["provenance"] == "synthetic" for r in ds["rows"])
        assert "synthetic" in ds["warning"]
        assert ds["llm_mode"] == config.llm_mode()


def test_invent_invalid_plan_rejected():
    resp = client.post("/api/datasets/invent", json={
        "session_id": "sess-api",
        "plan": {
            "research_type": "descriptive",
            "variables": [{"name": "x", "type": "numeric"}],
            "suggested_rows": 0,
            "data_plan": "x",
            "dataset_name": "x",
        },
        "rows": 50,
    })
    assert resp.status_code == 400


# ---------------------------------------------------------------- F3

def test_augment_happy_path():
    resp = client.post("/api/datasets/augment", json={
        "session_id": "sess-api",
        "csv": _messy_csv_b64(),
        "target_rows": 12,
        "filename": "survey.csv",
    })
    assert resp.status_code == 200, resp.text
    ds = resp.json()
    tags = [r["provenance"] for r in ds["rows"]]
    assert tags.count("original") == 4
    assert tags.count("augmented") == 8
    assert "original" in ds["warning"] and "augmented" in ds["warning"]


def test_augment_malformed_csv_rejected():
    resp = client.post("/api/datasets/augment", json={
        "session_id": "sess-api",
        "csv": "!!!not-base64!!!",
        "target_rows": 10,
    })
    assert resp.status_code == 400
    assert "base64" in resp.json()["detail"]


def test_augment_bad_target_rejected():
    resp = client.post("/api/datasets/augment", json={
        "session_id": "sess-api",
        "csv": _messy_csv_b64(),
        "target_rows": 0,
    })
    assert resp.status_code == 400


# ---------------------------------------------------------------- 2.10 real mode

REAL_MODE_AVAILABLE = bool(os.getenv("LLM_API_KEY"))


@pytest.mark.skipif(not REAL_MODE_AVAILABLE, reason="no LLM_API_KEY configured — mock mode is the verified baseline")
def test_real_mode_flows():
    plan = _scope(QUESTIONS[0])
    resp = client.post("/api/datasets/invent", json={
        "session_id": "sess-real", "plan": plan, "rows": 60,
    })
    assert resp.status_code == 200
    ds = resp.json()
    assert ds["llm_mode"] == "real"
    assert all(r["provenance"] == "synthetic" for r in ds["rows"])
