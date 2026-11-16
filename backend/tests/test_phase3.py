"""3.1–3.11 — Phase 3 tests: audit (F4), receipt (F5), export (F6),
contribution log (F11), variants (F8), source honesty (F9)."""

import base64
import io

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.engine import quality
from app.services import services
from app.main import app
from app.ai.receipt import compute_integrity_hash, render_variant, verify_integrity
from app.core.schemas import Dataset, DatasetRow, Provenance, Receipt
from app.core.storage import Storage

client = TestClient(app)

QUESTION = "Does study time affect exam scores?"


def _scope(session_id: str) -> dict:
    resp = client.post("/api/scope", json={"question": QUESTION, "session_id": session_id})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _invent(session_id: str, rows: int = 40) -> dict:
    plan = _scope(session_id)
    resp = client.post("/api/datasets/invent", json={"session_id": session_id, "plan": plan, "rows": rows})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _augment(session_id: str, target_rows: int = 20) -> dict:
    df = pd.DataFrame({
        "study_mode": ["group", "solo", "group", "solo"],
        "weekly_hours": [3, 5, None, 10],
        "quiz_score": [60, 70, 80, 90],
    })
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    csv_b64 = base64.b64encode(buf.getvalue().encode()).decode()
    resp = client.post("/api/datasets/augment", json={
        "session_id": session_id, "csv": csv_b64, "target_rows": target_rows, "filename": "s.csv",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


def _save_known_dataset() -> str:
    """Dataset with a known duplicate (2 identical rows out of 4)."""
    rows = [
        DatasetRow(values={"a": 1, "b": "x"}, provenance=Provenance.SYNTHETIC),
        DatasetRow(values={"a": 2, "b": "y"}, provenance=Provenance.SYNTHETIC),
        DatasetRow(values={"a": 3, "b": "z"}, provenance=Provenance.SYNTHETIC),
        DatasetRow(values={"a": 1, "b": "x"}, provenance=Provenance.SYNTHETIC),  # duplicate
    ]
    ds = Dataset(
        dataset_id="d_known", session_id="sess-known", name="known",
        rows=rows, schema={"columns": ["a", "b"]}, llm_mode="mock", adaption_mode="emulated",
    )
    Storage().save_dataset(ds)
    return ds.dataset_id


# ---------------------------------------------------------------- F4: audit

def test_audit_metrics_match_manual_computation():
    ds_id = _save_known_dataset()
    resp = client.get(f"/api/datasets/{ds_id}/audit")
    assert resp.status_code == 200, resp.text
    report = resp.json()
    # manual spot-check: 1 duplicate of 4 rows → 0.25
    assert report["metrics"]["duplicate_rate"]["after"] == pytest.approx(0.25)
    # independent engine recomputation on the same rows must agree
    df = pd.DataFrame([r.values for r in Storage().load_dataset(ds_id).rows])
    assert report["metrics"]["duplicate_rate"]["after"] == pytest.approx(quality.duplicate_rate(df))
    assert report["metrics"]["completeness"]["after"] == pytest.approx(quality.completeness(df))


def test_audit_before_after_pairing():
    ds = _augment("sess-audit", target_rows=20)
    resp = client.get(f"/api/datasets/{ds['dataset_id']}/audit")
    assert resp.status_code == 200, resp.text
    metrics = resp.json()["metrics"]
    for key in ("duplicate_rate", "near_duplicate_rate", "diversity", "completeness", "label_coverage"):
        assert "before" in metrics[key] and "after" in metrics[key]
    # baseline had a missing value → completeness must improve after cleaning
    assert metrics["completeness"]["after"] > metrics["completeness"]["before"]


def test_audit_without_baseline_notes_it():
    ds = _invent("sess-audit-nob", rows=30)
    resp = client.get(f"/api/datasets/{ds['dataset_id']}/audit")
    assert resp.status_code == 200
    metrics = resp.json()["metrics"]
    assert "note" in metrics["duplicate_rate"]
    assert metrics["duplicate_rate"]["before"] == metrics["duplicate_rate"]["after"]


def test_audit_interpretations_present():
    ds = _invent("sess-audit-int", rows=30)
    resp = client.get(f"/api/datasets/{ds['dataset_id']}/audit")
    report = resp.json()
    assert len(report["interpretation"]) >= 6  # 5 metric lines + sanity + verdict
    assert any("Overall:" in line for line in report["interpretation"])


def test_audit_unknown_dataset_404():
    resp = client.get("/api/datasets/d_nonexistent/audit")
    assert resp.status_code == 404


# ---------------------------------------------------------------- F5: receipt

def test_receipt_all_contract_fields_populated():
    ds = _invent("sess-rcpt", rows=20)
    resp = client.post("/api/receipts", json={
        "session_id": "sess-rcpt", "dataset_id": ds["dataset_id"], "source": "invented",
    })
    assert resp.status_code == 200, resp.text
    receipt = resp.json()
    assert receipt["receipt_id"].startswith("r_")
    f = receipt["fields"]
    for key in ("research_question", "dataset_source", "ai_tools_used", "generated_vs_student",
                "human_oversight_level", "student_contributions", "sources_consulted",
                "timestamp", "integrity_hash"):
        assert key in f, f"missing field: {key}"
    assert f["research_question"] == QUESTION
    assert f["dataset_source"] == "invented"
    assert f["human_oversight_level"] == "prompt_guided"
    assert f["integrity_hash"].startswith("sha256:")
    assert f["ai_tools_used"][0]["tool"] == "llm-mock"  # mode-accurate (mock is the verified baseline)


def test_receipt_hash_verifies_on_reload():
    ds = _invent("sess-rcpt-hash", rows=20)
    resp = client.post("/api/receipts", json={
        "session_id": "sess-rcpt-hash", "dataset_id": ds["dataset_id"], "source": "invented",
    })
    receipt_id = resp.json()["receipt_id"]
    stored = Storage().load_receipt(receipt_id)
    assert stored is not None
    assert verify_integrity(stored), "integrity hash must verify on reload"
    # tampering must be detectable
    tampered = stored.model_copy(deep=True)
    tampered.fields.research_question = "tampered question"
    assert not verify_integrity(tampered)


def test_receipt_no_fabricated_sources_in_mock_mode():
    """F9 honesty gate: receipts must never contain sources that weren't consulted."""
    ds = _invent("sess-rcpt-src", rows=20)
    resp = client.post("/api/receipts", json={
        "session_id": "sess-rcpt-src", "dataset_id": ds["dataset_id"], "source": "invented",
    })
    assert resp.status_code == 200
    sources = resp.json()["fields"]["sources_consulted"]
    assert sources == [], "mock-mode receipt must not fabricate sources"


def test_receipt_variants_change_layout():
    ds = _invent("sess-rcpt-var", rows=20)
    receipt = services.build_receipt_safe("sess-rcpt-var", ds["dataset_id"])
    standard = render_variant(receipt, "standard")
    journal = render_variant(receipt, "journal-style")
    teacher = render_variant(receipt, "teacher-check")
    assert standard["layout"] != journal["layout"] != teacher["layout"]
    assert "Integrity hash" in teacher["sections"]
    assert any("Human oversight" in k for k in journal["sections"])


def test_receipt_includes_contribution_log():
    ds = _invent("sess-rcpt-f11", rows=20)
    client.post("/api/sessions/sess-rcpt-f11/contributions", json={"action": "edited_rows", "detail": "fixed 3 values"})
    resp = client.post("/api/receipts", json={
        "session_id": "sess-rcpt-f11", "dataset_id": ds["dataset_id"], "source": "invented",
    })
    contributions = resp.json()["fields"]["student_contributions"]
    assert any(c["action"] == "edited_rows" for c in contributions)
    assert any(c["action"] == "plan_submitted" for c in contributions)  # auto-logged from invent


def test_receipt_rejects_unknown_dataset():
    resp = client.post("/api/receipts", json={
        "session_id": "s", "dataset_id": "d_nope", "source": "invented",
    })
    assert resp.status_code == 400


# ---------------------------------------------------------------- F6: export

def test_export_bundle_end_to_end():
    ds = _invent("sess-export", rows=20)
    client.post("/api/receipts", json={
        "session_id": "sess-export", "dataset_id": ds["dataset_id"], "source": "invented",
    })
    resp = client.get("/api/exports/sess-export")
    assert resp.status_code == 200, resp.text
    bundle = resp.json()
    assert set(bundle["files"]) == {"dataset.csv", "receipt.json", "methodology.md"}

    for name in bundle["files"]:
        fresp = client.get(f"/api/exports/sess-export/{name}")
        assert fresp.status_code == 200, f"{name} download failed"
        assert fresp.content, f"{name} is empty"

    # CSV keeps the provenance column and opens in pandas
    csv_resp = client.get("/api/exports/sess-export/dataset.csv")
    df = pd.read_csv(io.StringIO(csv_resp.content.decode()))
    assert "provenance" in df.columns
    assert (df["provenance"] == "synthetic").all()

    # receipt download is valid JSON with the contract fields
    r_resp = client.get("/api/exports/sess-export/receipt.json")
    assert "integrity_hash" in r_resp.json()["fields"]

    # methodology mentions the actual plan (dataset name + variables)
    m_resp = client.get("/api/exports/sess-export/methodology.md")
    text = m_resp.content.decode()
    assert ds["name"] in text
    assert "study" in text.lower() or "mode" in text.lower()


def test_export_auto_builds_receipt_when_missing():
    ds = _invent("sess-export-auto", rows=20)
    resp = client.get("/api/exports/sess-export-auto")
    assert resp.status_code == 200
    r_resp = client.get("/api/exports/sess-export-auto/receipt.json")
    assert r_resp.status_code == 200
    assert "integrity_hash" in r_resp.json()["fields"]


def test_export_unknown_session_404():
    resp = client.get("/api/exports/sess-nonexistent")
    assert resp.status_code == 404


def test_export_file_guard():
    resp = client.get("/api/exports/sess-export/evil.sh")
    assert resp.status_code == 400


# ---------------------------------------------------------------- F11 endpoint

def test_contribution_endpoint_roundtrip():
    resp = client.post("/api/sessions/sess-contrib/contributions", json={"action": "row_corrected", "detail": "fixed outlier"})
    assert resp.status_code == 200
    assert resp.json()["logged"] is True
    entries = Storage().get_contributions("sess-contrib")
    assert any(e["action"] == "row_corrected" for e in entries)
    assert all(e["timestamp"] for e in entries)


def test_contribution_empty_action_rejected():
    resp = client.post("/api/sessions/sess-contrib/contributions", json={"action": "   "})
    assert resp.status_code == 400
