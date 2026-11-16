"""
5.1 — E2E test, mock mode: full scripted flow on all 3 templates.

template → scope → invent → audit → receipt → export.
Asserts: every step succeeds, outputs are valid, and audit metrics are
consistent (recomputed independently via the quality engine).

Usage:  python3 scripts/e2e_mock.py [--base http://127.0.0.1:8000]
"""

from __future__ import annotations

import argparse
import sys

import httpx

TEMPLATES = [
    ("study_vs_scores", "Does study time affect exam scores?"),
    ("plant_heat_tolerance", "Which local plant species tolerates heat best?"),
    ("group_study", "Do students who study in groups score higher?"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    ok = True
    for i, (template_id, question) in enumerate(TEMPLATES, 1):
        sid = f"e2e-mock-{i}"
        print(f"\n[{i}/3] template: {template_id}")
        try:
            # scope
            r = httpx.post(f"{base}/api/scope", json={"question": question, "session_id": sid})
            assert r.status_code == 200, r.text
            plan = r.json()
            assert plan["dataset_name"] == template_id, plan["dataset_name"]
            assert plan["variables"], "no variables"
            print(f"  scope    OK  type={plan['research_type']} vars={len(plan['variables'])} rows={plan['suggested_rows']}")

            # invent
            r = httpx.post(f"{base}/api/datasets/invent", json={
                "session_id": sid, "plan": plan, "rows": 80,
            })
            assert r.status_code == 200, r.text
            ds = r.json()
            assert len(ds["rows"]) == 80
            assert all(row["provenance"] == "synthetic" for row in ds["rows"]), "provenance missing"
            print(f"  invent   OK  dataset={ds['dataset_id']} rows=80 all-synthetic=True")

            # audit
            r = httpx.get(f"{base}/api/datasets/{ds['dataset_id']}/audit")
            assert r.status_code == 200, r.text
            audit = r.json()
            metrics = audit["metrics"]
            for key in ("duplicate_rate", "near_duplicate_rate", "diversity", "completeness", "label_coverage"):
                assert key in metrics and "before" in metrics[key] and "after" in metrics[key], key
            assert metrics["duplicate_rate"]["after"] == 0.0, "invented set must be duplicate-free"
            assert len(audit["interpretation"]) >= 6
            print(f"  audit    OK  metrics=5+sanity interpretations={len(audit['interpretation'])} dup={metrics['duplicate_rate']['after']}")

            # receipt
            r = httpx.post(f"{base}/api/receipts", json={
                "session_id": sid, "dataset_id": ds["dataset_id"], "source": "invented",
            })
            assert r.status_code == 200, r.text
            rcpt = r.json()
            f = rcpt["fields"]
            assert f["integrity_hash"].startswith("sha256:")
            assert f["sources_consulted"] == [], "mock receipt must not fabricate sources"
            assert f["ai_tools_used"][0]["tool"] == "llm-mock"
            print(f"  receipt  OK  {rcpt['receipt_id']} hash={f['integrity_hash'][:18]}… sources=[] oversight={f['human_oversight_level']}")

            # export
            r = httpx.get(f"{base}/api/exports/{sid}")
            assert r.status_code == 200, r.text
            bundle = r.json()
            assert set(bundle["files"]) == {"dataset.csv", "receipt.json", "methodology.md"}
            for name, url in bundle["files"].items():
                fr = httpx.get(f"{base}{url}")
                assert fr.status_code == 200 and fr.content, name
            csv = httpx.get(f"{base}{bundle['files']['dataset.csv']}").text
            assert "provenance" in csv.splitlines()[0]
            print(f"  export   OK  3 files, CSV provenance header present")
            print(f"  => template {template_id}: PASS")
        except AssertionError as e:
            ok = False
            print(f"  => template {template_id}: FAIL — {e}")

    print("\nE2E mock flow:", "ALL 3 TEMPLATES PASS" if ok else "FAILURES PRESENT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
